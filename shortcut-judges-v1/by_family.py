import json,sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from judges import tfidf_cos
from collections import defaultdict
data,meta,key=sys.argv[1],sys.argv[2],sys.argv[3]
P=[json.loads(l) for l in open(data) if l.strip()]; M=[json.loads(l) for l in open(meta) if l.strip()]
assert len(P)==len(M)
cos=tfidf_cos([x for p in P for x in (p['prompt'],p['chosen'],p['rejected'])])
g=defaultdict(lambda:[0,0,0])
for p,m in zip(P,M):
    a,b=cos(p['prompt'],p['chosen']),cos(p['prompt'],p['rejected'])
    k=m.get(key); g[k][0]+=1; g[k][1]+= 1 if a>b else .5 if a==b else 0
    g[k][2]+= 1 if len(p['chosen'])>len(p['rejected']) else .5 if len(p['chosen'])==len(p['rejected']) else 0
for k in sorted(g,key=str): n,t,l=g[k]; print(f"{k}\tn={n}\ttfidf={t/n:.2f}\tlonger={l/n:.2f}")
