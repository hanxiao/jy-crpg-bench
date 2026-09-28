"""Cross-check draft claims against the catalogue, without trusting memory.

Run from paper/src:

    python3 check_consistency.py

Prints claim-vs-fact lines and exits nonzero if any claim contradicts the
run data it cites.
"""

import json
import os
import re
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(SRC, "figures", "catalog_snapshot.json")
MAIN = os.path.join(SRC, "main.tex")


sys.path.insert(0, os.path.join(SRC, "figures"))
import field


def load_rows():
    # every session on record: the paper credits a model with any rung any of
    # its sessions reached, so the checks run over all of them
    return field.load_runs(dedup=False)


def claim(name, condition, fact):
    flag = "OK   " if condition else "CONTRADICTS "
    print("%s %s: %s" % (flag, name, fact))
    return condition


def main():
    rows = load_rows()
    scored = field.played(rows)
    read = [r for r in scored if r.get("bigmap") is not None]
    main_tex = open(MAIN, encoding="utf-8").read()
    ok = True

    # every numeric claim about map latching must match the generated stats
    latched = sum(1 for r in scored if r.get("bigmap") is True)
    corrob = sum(1 for r in scored if r.get("bigmap") is True and r.get("exit_secs") is not None)
    ok &= claim("map latches",
               ("none clears any later rung" not in main_tex) or (latched == 0),
               "%d latched, %d corroborated" % (latched, corrob))

    # progression claims: experience is read from the save and the replay, and the
    # prose credits it to exactly the sessions field.rungs_of credits
    EXPK = field.DEFINITION.index("gained\nexperience")
    prog = [r["id"] for r in scored if field.rungs_of(r)[EXPK] is True]
    ok &= claim("progression floor", "No model gains" not in main_tex and "none wins a battle" not in main_tex
                and "the only session that wins a battle" in " ".join(main_tex.split()) and len(prog) == 1,
                "sessions that gained experience: %s" % prog)

    # no hardcoded run ratios in prose (they must come from macros)
    stray = re.findall(r"\b0\.\d{3}\b", main_tex)
    ok &= claim("hardcoded ratios", len(stray) == 0, "matches: %s" % (sorted(set(stray)) if stray else "none"))

    # inputs referenced must exist on disk
    missing = []
    for i in re.findall(r"\\input\{([^}]*)\}", main_tex):
        path = i if i.endswith(".tex") else i + ".tex"
        if not os.path.exists(os.path.join(SRC, path)):
            missing.append(path)
    ok &= claim("inputs present", not missing, "%s" % (missing if missing else "none"))

    # citations referenced must resolve in refs.bib
    bib = open(os.path.join(SRC, "refs.bib"), encoding="utf-8").read()
    keys = {k for k in re.findall(r"@\w+\{([^,\s]+),", bib)}
    cited = set()
    for grp in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]*)\}", main_tex):
        cited.update(x.strip() for x in grp.split(","))
    ghost = sorted(cited - keys)
    ok &= claim("citations resolve", not ghost, "missing: %s" % ghost)

    # Typed claims about named runs in Section 4, each tied to the phrase that
    # makes it, so a regenerated field that no longer supports a sentence fails
    # here instead of going out in print.
    flat = re.sub(r"\s+", " ", main_tex)
    models = [r for r in scored if not field.is_random(r["agent"])]
    active = [r for r in models if r["actions"] >= 30]
    randoms = field.random_rows(rows)
    rk = sum(round(r["meaningful"] * r["actions"]) for r in randoms)
    rn = sum(r["actions"] for r in randoms)
    floor = rk / rn if rn else None
    if "the first milestone a random walk does not reach" in flat:
        ok &= claim("random never on the map", bool(randoms) and not any(field.on_map(r) for r in randoms),
                    "%d random runs" % len(randoms))
    on_map = [r for r in scored if field.on_map(r)]
    if "reach the world map" in flat:
        saved_map = {r["agent"] for r in on_map
                     if r.get("saved_at") is not None or r.get("world_map_at") is not None or r.get("slot_saved") is True}
        ok &= claim("every model's world-map credit has a save behind it in some session",
                    {r["agent"] for r in on_map} <= saved_map,
                    "%d sessions on the map, %d models save-backed" % (len(on_map), len(saved_map)))
    holders = [r for r in models if r.get("compass")]
    if "every milestone any of its sessions reached" in flat:
        union = {m["agent"]: m for m in field.model_rows(models)}
        ok &= claim("a model's rung is the union over its sessions",
                    all(union[a]["rungs"][k] is (True if any(field.rungs_of(r)[k] is True for r in models if r["agent"] == a) else union[a]["rungs"][k])
                        for a in union for k in range(len(field.DEFINITION))),
                    "%d models, %d sessions" % (len(union), len(models)))
        H, C, F, D = (field.DEFINITION.index(x) for x in ("spoke with\nthe hermit", "held the\ncompass", "entered\na battle", "ended\na battle"))
        ok &= claim("the compass is never held without the hermit's conversation",
                    all(m["rungs"][H] for m in union.values() if m["rungs"][C]),
                    "compass %s" % [a for a, m in union.items() if m["rungs"][C]])
        ok &= claim("a fight fought to the end was entered",
                    all(m["rungs"][F] for m in union.values() if m["rungs"][D]),
                    "fought out %s" % [a for a, m in union.items() if m["rungs"][D]])
    if "two take the compass, enter a battle and see it end" in flat:
        FIGHT, CMP = field.DEFINITION.index("entered\na battle"), field.DEFINITION.index("held the\ncompass")
        past = [m["agent"] for m in field.model_rows(models) if m["rungs"][FIGHT] is True and m["rungs"][CMP] is True]
        ok &= claim("two models take the compass and enter a fight", len(past) == 2, "%s" % past)
    # session and compared with the macros the prose reads
    nums = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                           open(os.path.join(SRC, "figures", "numbers.tex"), encoding="utf-8").read()))
    by_model = {}
    for r in models:
        by_model.setdefault(r["agent"], []).append(r)
    if "cross in every session they played" in flat:
        every = sorted(a for a, rs in by_model.items() if all(field.on_map(r) for r in rs))
        crossed = sum(1 for r in models if field.on_map(r))
        ok &= claim("sessions crossed and models crossing every time match the macros",
                    (int(nums["LcrossSessions"]), int(nums["LcrossEvery"])) == (crossed, len(every)),
                    "%d of %d sessions crossed, every time: %s" % (crossed, len(models), every))
    if "reached him in every one of its" in flat:
        H = field.DEFINITION.index("spoke with\nthe hermit")
        FIGHT = field.DEFINITION.index("entered\na battle")
        top = [nums["LsecondLabel"].replace("\\texttt{", "").rstrip("}")]
        hermit = {a: sum(1 for r in rs if field.rungs_of(r)[H] is True) for a, rs in by_model.items()}
        others = {a: n for a, n in hermit.items() if n and a not in top}
        ok &= claim("the second model reached the hermit in every session, the others in at most half of theirs",
                    hermit[top[0]] == len(by_model[top[0]])
                    and int(nums["LhermitOthers"]) == len(others)
                    and max(n / len(by_model[a]) for a, n in others.items()) == 0.5,
                    "top %s %s, others %s" % (top, {a: (hermit[a], len(by_model[a])) for a in top}, {a: (n, len(by_model[a])) for a, n in others.items()}))
    if "agrees with the count the service recorded" in flat:
        both = [r for r in models if r.get("exit_acts") is not None and (r.get("replay") or {}).get("crossing_actions") is not None]
        ok &= claim("replay and service crossing counts agree on every session carrying both",
                    bool(both) and len(both) == int(nums["LcrossAgree"])
                    and all(r["exit_acts"] == r["replay"]["crossing_actions"] for r in both),
                    "%d sessions carry both" % len(both))
    if "share of sessions in which each model reached each milestone" in flat:
        union = {m["agent"]: m for m in field.model_rows(models)}
        ok &= claim("every marker share is read from every session and agrees with the credit",
                    all(c[1] == c[2] for m in union.values() for c in m["counts"])
                    and all((m["rungs"][k] is True) == (m["counts"][k][0] > 0)
                            for m in union.values() for k in range(len(field.DEFINITION))),
                    "%d models, %d cells" % (len(union), sum(len(m["counts"]) for m in union.values())))
    if "with a light dot per session and a black dot for the mean" in flat:
        union = field.model_rows(models)
        ok &= claim("each box plot holds one count per session that crossed",
                    all(len(m["crossings"]) == sum(1 for r in by_model[m["agent"]] if field.on_map(r))
                        and m["crossings"] == sorted(a for a in (field.crossing_actions(r) for r in by_model[m["agent"]]) if a is not None)
                        for m in union),
                    "%s" % {m["agent"]: len(m["crossings"]) for m in union})
    if "whose inventory shows a new item also shows the item message" in flat:
        bag = [r for r in scored if r.get("picked_item")]
        ok &= claim("every inventory pickup also shows the item message",
                    bool(bag) and all((r.get("replay") or {}).get("obtained", {}).get("seconds") for r in bag)
                    and int(nums["PobtainedBag"]) == len(bag),
                    "%d sessions whose inventory shows a new item" % len(bag))
    def seen(r, n):
        e = r.get("replay") or {}
        return bool(e.get(n) and e[n]["seconds"] > 0)
    if "shows the coordinate line on the replay, and no other session does" in flat:
        cb = [r for r in scored if r.get("replay") and r.get("compass") is not None]
        ok &= claim("the compass panel and the bag agree in both directions",
                    bool(cb) and all(seen(r, "compass") == bool(r["compass"]) for r in cb)
                    and (int(nums["PcompassBoth"]), int(nums["PcompassBag"])) == (len(cb), sum(1 for r in cb if r["compass"])),
                    "%d sessions with both, %d with the compass" % (len(cb), sum(1 for r in cb if r["compass"])))
    if "also shows his portrait on the replay" in flat:
        hb = [r for r in scored if r.get("replay") and r.get("world_opened") is not None]
        ok &= claim("every save with the hermit's scenes opened has his portrait on the replay",
                    bool(hb) and not any(r["world_opened"] and not seen(r, "hermit") for r in hb)
                    and (int(nums["PhermitBoth"]), int(nums["PhermitOpened"])) == (len(hb), sum(1 for r in hb if r["world_opened"])),
                    "%d sessions with both, %d opened" % (len(hb), sum(1 for r in hb if r["world_opened"])))
    if "the five held templates score at least" in flat:
        ev = [r["replay"] for r in scored if r.get("replay")]
        def span(panels):
            miss = max(e[n]["max"] for e in ev for n in panels if e[n]["seconds"] == 0 and e[n]["max"] is not None)
            hit = min(e[n]["max"] for e in ev for n in panels if e[n]["seconds"] > 0)
            return miss, hit
        (hm, hh), (mm, mh) = span(("hermit", "compass", "battle", "defeat", "prompt")), span(("obtained", "won", "exp", "level"))
        t = float(nums["ReplayThreshold"])
        ok &= claim("the replay threshold sits between the highest miss and the lowest hit, for held panels and messages",
                    hm < t <= hh and mm < t <= mh
                    and all(abs(float(nums[k]) - v) < 0.006 for k, v in (("ReplayMissMax", hm), ("ReplayHitMin", hh), ("ReplayMsgMissMax", mm), ("ReplayMsgHitMin", mh))),
                    "held %.3f/%.3f, messages %.3f/%.3f, threshold %s" % (hm, hh, mm, mh, nums["ReplayThreshold"]))
    if "models entered a location" in flat:
        SCENE = field.DEFINITION.index("entered\na location")
        union = field.model_rows(models)
        entered = [m["agent"] for m in union if m["rungs"][SCENE] is True]
        ok &= claim("the scene milestone is read for every session and the count matches the macro",
                    all(c[1] == c[2] for m in union for c in [m["counts"][SCENE]])
                    and (int(nums["Lscene"]), int(nums["LnoScene"])) == (len(entered), len(union) - len(entered)),
                    "%d models entered a scene: %s" % (len(entered), entered))
    # The four-hour sessions that count, validated against the manifest.
    import long_cohort
    attempts = field.long_attempts()
    manifest = long_cohort.validate(attempts)
    long_rows = field.load_long()
    selected_ids = {r["id"] for r in long_rows}
    table = open(os.path.join(SRC, "tables/long.tex"), encoding="utf-8").read()
    table_ids = re.findall(r"^% counted-session: ([0-9a-f]{12})$", table, re.M)
    visible_table = "\n".join(line for line in table.splitlines() if not line.startswith("%"))
    ok &= claim("the counted rows match the audit IDs exactly",
                set(table_ids) == selected_ids and len(table_ids) == len(selected_ids), str(sorted(table_ids)))
    visible_rows = [line for line in visible_table.splitlines() if " & " in line and not line.startswith("Model &")]
    ok &= claim("all counted runs use the same table without review rows",
                len(visible_rows) == len(long_rows) and "Pending review" not in visible_table
                and "review-session:" not in table and "\\dagger" not in visible_table, str(len(visible_rows)))
    ok &= claim("session identifiers are hidden from the displayed table",
                "Session &" not in visible_table and not re.search(r"[0-9a-f]{12}", visible_table), "IDs remain in source comments and manifest")
    ok &= claim("the four-hour model count matches the macro", int(nums["NlongModels"]) == len({r["agent"] for r in long_rows}), str(len(long_rows)))
    ok &= claim("attempt and submission counts match generated macros",
                (int(nums["NlongAttempts"]), int(nums["NlongSessions"]), int(nums["NlongWithheld"]))
                == (len(attempts), len(long_rows), len(attempts) - len(long_rows)), str(len(attempts)))
    ok &= claim("the attempt that read earlier sessions does not count", field.HACK_SESSION not in selected_ids, field.HACK_SESSION)
    for rung in ("gained\nexperience", "one of the\nfourteen"):
        k = field.DEFINITION.index(rung)
        ok &= claim("no four-hour session that counts reached " + rung.replace("\n", " "),
                    not any(field.rungs_of(r)[k] is True for r in long_rows), str(len(long_rows)))
    if "sessions before the hour" in flat:
        idle = sum(1 for r in models if r.get("reason") == "idle")
        ok &= claim("the idle-ended session count matches the macro", idle > 0 and int(nums["NidleSessions"]) == idle,
                    "%d idle-ended" % idle)
    # The human references of Figure 3, read from human_sessions.json.
    if "cross onto the world map within the first minute" in flat:
        speed = [v for v in field.human_videos() if v["class"] == "speedrun"]
        ok &= claim("every speedrun crosses within the first minute",
                    bool(speed) and all(v["milestones_min"]["map"] is not None and v["milestones_min"]["map"] < 1 for v in speed),
                    "%s" % [v["milestones_min"]["map"] for v in speed])
    if "human references are read from published videos" in flat:
        vids = field.human_videos()
        ok &= claim("every human video carries a reading for every milestone and its steps",
                    bool(vids) and all(set(v["milestones_min"]) == set(field.HUMAN_KEYS) and v.get("steps_to_map") is not None for v in vids),
                    "%d videos" % len(vids))
    if "all of which finish the game" in flat:
        speed = [v for v in field.human_videos() if v["class"] == "speedrun"]
        ok &= claim("every speedrun finishes the game",
                    bool(speed) and all(v.get("completion_min") is not None for v in speed),
                    "%s" % [v.get("completion_min") for v in speed])
    if "one of which reaches the ending" in flat:
        plays = [v for v in field.human_videos() if v["class"] == "playthrough"]
        ok &= claim("exactly one playthrough reaches the ending",
                    sum(1 for v in plays if v.get("completion_min") is not None) == 1,
                    "%s" % [v.get("completion_min") for v in plays])
    if "in which a human speedrun finishes the game" in flat:
        speed = [v for v in field.human_videos() if v["class"] == "speedrun"]
        ok &= claim("a speedrun finishes the game within the hour budget",
                    any(v.get("completion_min") is not None and v["completion_min"] <= field.DEFAULT_BUDGET / 60 for v in speed),
                    "%s" % [v.get("completion_min") for v in speed])

    print("\n%d runs scored, %d sessions with a map verdict, %d maps latched"
          % (len(scored), len(read), latched))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
