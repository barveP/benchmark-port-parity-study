#!/usr/bin/env python3
"""Descriptive pass over harbor adapters/*/parity_experiment.json; prints to stdout. Usage: parity_summary.py <harbor_clone_dir>"""
import json, glob, sys, os, re, collections, statistics as st
root=sys.argv[1]
files=sorted(glob.glob(os.path.join(root,'adapters','*','parity_experiment.json')))
n_entries=0; runs=collections.Counter(); subset=0; full=0; unknown=0
metrics=0; with_runs=0; run_len=collections.Counter(); bad=[]
keys=collections.Counter(); floor=[]; single=[]; gaps=[]
for f in files:
    name=f.split(os.sep)[-2]
    try: d=json.load(open(f))
    except Exception as e:
        bad.append((name,str(e)[:80])); continue
    if isinstance(d,dict): d=[d]
    for e in d:
        n_entries+=1
        runs[str(e.get('number_of_runs',e.get('number_of_trials')))]+=1
        a=e.get('adapted_benchmark_size'); p=e.get('parity_benchmark_size')
        if isinstance(a,(int,float)) and isinstance(p,(int,float)):
            if p<a: subset+=1
            else: full+=1
        else: unknown+=1
        for m in e.get('metrics',[]) or []:
            metrics+=1
            for k in m: keys[k]+=1
            sides={k:v for k,v in m.items() if k.endswith('_runs') and isinstance(v,list)}
            if sides: with_runs+=1
            vals={}
            for k,v in sides.items():
                nums=[x for x in v if isinstance(x,(int,float))]
                run_len[len(v)]+=1
                if nums: vals[k]=nums
            if len(vals)>=2:
                ks=sorted(vals)
                o=vals.get('original_runs'); h=vals.get('harbor_runs')
                if o and h:
                    mo=st.mean(o); mh=st.mean(h)
                    gaps.append((abs(mo-mh),name,m.get('metric'),len(o),len(h),round(mo,3),round(mh,3)))
                    if mo==0 and mh==0: floor.append((name,m.get('metric'),e.get('agent'),e.get('model')))
                    if len(o)==1 or len(h)==1: single.append(name)
print('files',len(files),'unparseable',bad)
print('entries',n_entries,'metrics',metrics,'metrics with *_runs lists',with_runs)
print('number_of_runs distribution',dict(sorted(runs.items(), key=lambda x:-x[1])))
print('parity set: subset',subset,'full',full,'unknown/non-numeric',unknown)
print('run-list lengths',dict(sorted(run_len.items())))
print('metric keys',dict(keys.most_common(14)))
print('metrics with original_runs+harbor_runs both numeric:',len(gaps))
print('  both means exactly 0 (floor):',floor)
print('  adapters with a single run on a side:',sorted(set(single)))
