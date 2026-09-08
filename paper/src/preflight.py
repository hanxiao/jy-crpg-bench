import json,os,re,subprocess,sys
SRC=os.path.abspath('.')
def ok(msg): print("OK   "+msg)
def bad(msg): print("FAIL "+msg)

# regenerate everything
for cmd in ([sys.executable,"figures/make.py"],[sys.executable,"figures/make_metrics.py"],
            [sys.executable,"figures/emit_numbers.py"]):
    r=subprocess.run(cmd,cwd=SRC,capture_output=True,text=True)
    if r.returncode: bad(" ".join(cmd)+" -> "+r.stderr[-400:]); sys.exit(1)
ok("regenerated")

main=open('main.tex',encoding='utf-8').read()
defined={}
for f in ('figures/numbers.tex','tables/runs.tex','tables/family.tex'):
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
play=[r for r in cat if r['budget']==1200 and (r['actions'] or 0)>0]
facts={
 'runs_scored':len(play),
 'probes':[r['agent'] for r in cat if r['agent'].startswith('probe-')],
 'never':[r['agent'] for r in cat if not (r['actions'] or 0)],
 'latched':sum(1 for r in play if r.get('bigmap')),
 'corroborated':sum(1 for r in play if r.get('bigmap') and r.get('exit_secs')),
 'max_exp':max((r.get('exp') or 0) for r in play),
 'manyratio_at_20min':[r['agent'] for r in play if r['meaningful']>=0.5],
}
print("catalogue facts:",json.dumps(facts,indent=None))
if all((r.get('level')==1 for r in play)): bad("every scored run is level 1 -- § claims this; confirm")
print("cited keys:",len(cites),"| unused in bib:",unused)
print("numbers.tex macros:",len(allproj))
if problems:
    print("\nPROBLEMS:"); [print("  - "+p) for p in problems]
else:
    print("\nno problems detected")
