"""Build the default review copy and verify that identity links stay out of the PDF."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
FORBIDDEN = re.compile(
    r"han\s+xiao|yiming\s+liu|han\.xiao|letusgo126|"
    r"github\.com/hanxiao|hanxiao\.io",
    re.IGNORECASE,
)


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        sys.stderr.write(result.stdout)
        raise SystemExit(result.returncode)
    return result.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jy-crpg-blind-") as directory:
        out = Path(directory)
        run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={out}", "main.tex"],
            cwd=SRC,
        )
        env = dict(os.environ)
        env["BIBINPUTS"] = str(SRC) + os.pathsep + env.get("BIBINPUTS", "")
        env["BSTINPUTS"] = str(SRC) + os.pathsep + env.get("BSTINPUTS", "")
        run(["bibtex", "main"], cwd=out, env=env)
        for _ in range(2):
            run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                 f"-output-directory={out}", "main.tex"],
                cwd=SRC,
            )
        text_path = out / "main.txt"
        run(["pdftotext", "-layout", str(out / "main.pdf"), str(text_path)], cwd=SRC)
        text = text_path.read_text(encoding="utf-8", errors="replace")
        if "Anonymous authors" not in text:
            raise SystemExit("blind build did not contain the anonymous title block")
        matches = sorted(set(FORBIDDEN.findall(text)))
        if matches:
            raise SystemExit("blind build leaked sensitive text: " + ", ".join(matches))
    print("blind build passed: anonymous title block and sensitive-text scan are clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
