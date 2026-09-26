import json,os,re,subprocess,sys
SRC=os.path.abspath('.')
def ok(msg): print("OK   "+msg)
def bad(msg): print("FAIL "+msg)

# regenerate everything
# Generators that write their own files, then the two that print their file
# to stdout, which is written for them: a captured stdout is not a file.
for cmd in ([sys.executable,"figures/make.py"],[sys.executable,"figures/make_metrics.py"],[sys.executable,"figures/filters.py"]):
    r=subprocess.run(cmd,cwd=SRC,capture_output=True,text=True)
    if r.returncode: bad(" ".join(cmd)+" -> "+r.stderr[-400:]); sys.exit(1)
for script,target in (("figures/recover_sessions.py","figures/recovered_sessions.json"),
                      ("figures/emit_numbers.py","figures/numbers.tex"),
                                            ("figures/emit_books.py","tables/books.tex"),
                      ("figures/emit_effort.py","tables/effort.tex"),
                      ("figures/emit_milestones.py","tables/milestones.tex"),
                      ("figures/emit_long.py","tables/long.tex"),
                      ("figures/emit_battles.py","tables/battles.tex"),
                      ("figures/emit_instructions.py","tables/instructions.tex")):
    r=subprocess.run([sys.executable,script],cwd=SRC,capture_output=True,text=True)
    if r.returncode: bad(script+" -> "+r.stderr[-400:]); sys.exit(1)
    open(os.path.join(SRC,target),"w",encoding="utf-8").write(r.stdout)
ok("regenerated")
r = subprocess.run([sys.executable, "-B", "figures/test_priority_metrics.py"],
                   cwd=SRC, capture_output=True, text=True)
if r.returncode:
    bad("figure/table metric regression checks -> " + r.stdout + r.stderr)
    sys.exit(1)
ok("figure/table metric regression checks")

main=open('main.tex',encoding='utf-8').read()
defined={}
for f in ('figures/numbers.tex','tables/books.tex','tables/effort.tex','tables/milestones.tex','tables/long.tex'):
    if not os.path.exists(f): bad("missing "+f); sys.exit(1)
    defined[f]=set(re.findall(r'\\newcommand\{\\(\w+)\}',open(f).read()))
    if ('\\input{'+f+'}' not in main) and ('\\input{'+f.replace('.tex','')+'}' not in main):
        bad(f+" is generated but main.tex never inputs it")
used=set(re.findall(r'\\([A-Za-z]\w*)',main))
macro_defined=set(re.findall(r'\\newcommand\{\\(\w+)\}',main))
allproj=macro_defined|{k for s in defined.values() for k in s}
bibkeys=set(re.findall(r'@\w+\{(\w+),',open('refs.bib',encoding='utf-8').read()))
cites=set()
for grp in re.findall(r'\\cite[pt]?\{([^}]*)\}',main):
    cites.update(x.strip() for x in grp.split(','))
problems=[]
# used-but-undefined macros from generated files
if not defined.get('figures/numbers.tex'):
    problems.append("numbers.tex defines no macros")
ghost=[c for c in sorted(cites) if c not in bibkeys]
if ghost: problems.append("cites not in refs.bib: "+", ".join(ghost))
unused=[k for k in sorted(bibkeys) if k not in cites]

# fact checks against the catalogue
cat=json.load(open('figures/catalog_snapshot.json'))
sys.path.insert(0,'figures'); import field
play=[r for r in cat if r['budget']==field.DEFAULT_BUDGET and (r['actions'] or 0)>0]
facts={
 'runs_scored':len(play),
 'probes':[r['agent'] for r in cat if r['agent'].startswith('probe-')],
 'never':[r['agent'] for r in cat if not (r['actions'] or 0)],
 'latched':sum(1 for r in play if r.get('bigmap')),
 'corroborated':sum(1 for r in play if r.get('bigmap') and r.get('exit_secs')),
 'ratio_at_least_half':[r['agent'] for r in play if r['meaningful']>=0.5],
}
print("catalogue facts:",json.dumps(facts,indent=None))
print("cited keys:",len(cites),"| unused in bib:",unused)
print("numbers.tex macros:",len(allproj))
# anonymity: while \iclrfinalcopy is commented out, no source may name an
# author, an address or the project (the scan of PR #48, on the sources since
# pdftotext is not on every build machine; the screenshots are checked by eye)
import glob
if not re.search(r'^\s*\\iclrfinalcopy', main, re.M):
    leak = re.compile(r'hanxiao|jina\.ai|letusgo|Han Xiao|Yiming', re.I)
    for f in ['main.tex'] + sorted(glob.glob('figures/*.tex')):
        text = re.sub(r'(?m)(?<!\\)%.*$', '', open(f, encoding='utf-8').read())
        for m in leak.finditer(text):
            problems.append(f"anonymity: {f} contains {m.group(0)!r}")
    ok("anonymity scan of the sources")
if problems:
    print("\nPROBLEMS:"); [print("  - "+p) for p in problems]
else:
    print("\nno problems detected")
