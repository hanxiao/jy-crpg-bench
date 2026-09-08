import json, os, statistics as st, collections
CAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog_snapshot.json")
rows = json.load(open(CAT, encoding='utf-8'))
rows = [r for r in rows if not r['agent'].startswith('probe-')]
play = [r for r in rows if r['budget'] == 1200 and (r['actions'] or 0) > 0]

print("== repetition over identical labels ==")
groups = collections.defaultdict(list)
for r in play:
    groups[r['agent']].append(r)
for lab, g in groups.items():
    if len(g) > 1:
        rs = [round(r['meaningful'], 3) for r in g]
        ac = [r['actions'] for r in g]
        sd = st.stdev(rs) if len(rs) > 1 else 0.0
        print(f"{lab:26s} n={len(g)} actions={ac} ratios={rs} sd={sd:.3f}")
singles = sorted([lab for lab, g in groups.items() if len(g) == 1])
print("single-session labels:", len(singles))
for s in singles:
    print("   ", s)

print()
print("== action space actually used ==")
hist = collections.Counter()
for r in play:
    hist.update(r.get('keys') or {})
tot = sum(hist.values())
diag = {'kp7', 'kp9', 'kp1', 'kp3'}
arrows = {'up', 'down', 'left', 'right'}
d = sum(v for k, v in hist.items() if k in diag)
a = sum(v for k, v in hist.items() if k in arrows)
print("total key events:", tot, "| diagonals:", d, f"({d/tot:.1%})", "| arrows:", a, f"({a/tot:.1%})")
print("other keys:", dict((k, v) for k, v in hist.most_common() if k not in diag | arrows))

print()
print("== scene-crossing evidence ==")
ex = [r for r in play if r.get('exit_secs') is not None]
big = [r for r in play if r.get('bigmap') is True]
print("sessions with first-transition clock:", len(ex))
for r in ex:
    print(f"   {r['agent']:26s} {r['exit_secs']:>7}s at action {r['exit_acts']}")
print("median:", st.median(r['exit_secs'] for r in ex), "s;", st.median(r['exit_acts'] for r in ex), "actions")
print("bigmap-true sessions:", len(big), "| corroborated by a black frame:", sum(1 for r in big if r.get('exit_secs') is not None))
print("bigmap unmeasured:", sum(1 for r in play if r.get('bigmap') is None), "of", len(play))

print()
print("== volume ==")
mod = [r for r in play if 'random' not in r['agent'].lower()]
print("model sessions:", len(mod), "actions:", sum(r['actions'] for r in mod),
      "reads:", sum(r['reads'] for r in mod), "hours played:", round(sum(r['played'] for r in play) / 3600, 2))
print("labels in all sessions:", len({r['agent'] for r in rows}))
