import io
t = io.open('out.txt', encoding='utf-8', errors='ignore').read()
probes = ["Leaderboard aggregated", "deliberately not the headline", "act/min", "ratio [95", "claude-fable-5-1", "0.631", "0.403"]
print("probe counts:")
for probe in probes:
    print("  %-32s %d" % (probe, t.count(probe)))
i = t.find("Leaderboard aggregated")
if i >= 0:
    print("\ncaption window:")
    print(t[i:i + 500].replace('\n', ' '))
