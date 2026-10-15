#!/usr/bin/env python3
"""Check Harbor's own parity 'matching criterion' (run-score ranges overlap) on adapters/*/parity_experiment.json.
Descriptive pass; prints to stdout. Usage: parity_overlap.py <harbor_clone_dir>"""
import json, glob, sys, os, statistics as st, collections
root=sys.argv[1]
rows=[]
for f in sorted(glob.glob(os.path.join(root,'adapters','*','parity_experiment.json'))):
    name=f.split(os.sep)[-2]
    d=json.load(open(f))
    if isinstance(d,dict): d=[d]
    for ei,e in enumerate(d):
        for m in e.get('metrics',[]) or []:
            def runs(prefixes):
                for p in prefixes:
                    for suf in ('_runs','_trials'):
                        v=m.get(p+suf)
                        if isinstance(v,list):
                            nums=[x for x in v if isinstance(x,(int,float)) and not isinstance(x,bool)]
                            if nums: return nums
                return None
            a=runs(['original']); b=runs(['harbor'])
            if a is None or b is None:
                rows.append((name,ei,m.get('metric'),'no-paired-runs',None,None,None)); continue
            overlap = max(a)>=min(b) and max(b)>=min(a)
            status='overlap' if overlap else 'NO-OVERLAP'
            if len(a)<2 or len(b)<2: status+='(k<2)'
            rows.append((name,ei,m.get('metric'),status,a,b,abs(st.mean(a)-st.mean(b))))
c=collections.Counter(r[3] for r in rows)
print('metric rows:',len(rows)); print(dict(c))
adapters_no=sorted({r[0] for r in rows if r[3].startswith('NO-OVERLAP')})
print('adapters with >=1 metric failing range-overlap:',len(adapters_no),adapters_no)
identical=[r for r in rows if r[4] and r[5] and r[4]==r[5]]
print('metric rows where original_runs == harbor_runs exactly:',len(identical), sorted({r[0] for r in identical}))
zero_var=[r for r in rows if r[4] and r[5] and len(r[4])>=2 and len(set(r[4]))==1 and len(set(r[5]))==1]
print('rows with zero variance on both sides (k>=2):',len(zero_var))
print('--- NO-OVERLAP rows ---')
for r in rows:
    if r[3].startswith('NO-OVERLAP'):
        print(r[0],'|',r[2],'|',r[3],'| orig',r[4],'| harbor',r[5])
