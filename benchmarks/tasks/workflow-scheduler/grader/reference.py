from __future__ import annotations

from collections import defaultdict, deque


def _validate(workflow):
    if not isinstance(workflow, dict): raise ValueError("workflow must be an object")
    if not isinstance(workflow.get("workflow_id"), str) or not workflow["workflow_id"]: raise ValueError("workflow_id")
    workers=workflow.get("workers")
    if type(workers) is not int or workers < 1: raise ValueError("workers")
    tasks=workflow.get("tasks")
    if not isinstance(tasks,list) or not tasks: raise ValueError("tasks")
    by_id={}
    for t in tasks:
        if not isinstance(t,dict): raise ValueError("task")
        ident=t.get("id"); duration=t.get("duration"); maximum=t.get("max_attempts",1); failures=t.get("fail_attempts",0)
        if not isinstance(ident,str) or not ident or ident in by_id: raise ValueError("id")
        if type(duration) is not int or duration < 1: raise ValueError("duration")
        if type(maximum) is not int or maximum < 1: raise ValueError("max_attempts")
        if type(failures) is not int or failures < 0 or failures > maximum: raise ValueError("fail_attempts")
        deps=t.get("depends_on",[])
        if not isinstance(deps,list) or any(not isinstance(d,str) for d in deps) or len(set(deps)) != len(deps): raise ValueError("depends_on")
        by_id[ident]=dict(t,depends_on=deps,max_attempts=maximum,fail_attempts=failures)
    for ident,t in by_id.items():
        if ident in t["depends_on"] or any(d not in by_id for d in t["depends_on"]): raise ValueError("dependency")
    indegree={i:len(t["depends_on"]) for i,t in by_id.items()}; children=defaultdict(list)
    for i,t in by_id.items():
        for d in t["depends_on"]: children[d].append(i)
    q=deque(i for i,n in indegree.items() if n==0); seen=0
    while q:
        i=q.popleft();seen+=1
        for child in children[i]:
            indegree[child]-=1
            if indegree[child]==0:q.append(child)
    if seen!=len(by_id):raise ValueError("cycle")
    return by_id


def run_reference(workflow):
    tasks=_validate(workflow); now=0; running=[]; states={i:"pending" for i in tasks}; attempts={i:0 for i in tasks}; first={i:None for i in tasks}; finished={i:None for i in tasks}; retry_at={i:0 for i in tasks}; events=[]
    while any(s not in {"succeeded","failed","skipped"} for s in states.values()):
        # First make descendants of permanently failed jobs terminal.
        changed=True
        while changed:
            changed=False
            for ident in sorted(tasks):
                if states[ident]=="pending" and any(states[d] in {"failed","skipped"} for d in tasks[ident]["depends_on"]):
                    states[ident]="skipped";finished[ident]=now;events.append({"time":now,"event":"skipped","task_id":ident,"attempt":0});changed=True
        # Complete everything scheduled at this timestamp in ID order.
        ended=sorted((r for r in running if r[0]==now),key=lambda r:r[1]);running=[r for r in running if r[0]!=now]
        for end,ident,attempt in ended:
            t=tasks[ident]
            if attempt<=t["fail_attempts"]:
                if attempt>=t["max_attempts"]:
                    states[ident]="failed";finished[ident]=now;events.append({"time":now,"event":"failed","task_id":ident,"attempt":attempt})
                else:
                    states[ident]="retry_wait";retry_at[ident]=now+2**(attempt-1);events.append({"time":now,"event":"retry","task_id":ident,"attempt":attempt})
            else:
                states[ident]="succeeded";finished[ident]=now;events.append({"time":now,"event":"succeeded","task_id":ident,"attempt":attempt})
        changed=True
        while changed:
            changed=False
            for ident in sorted(tasks):
                if states[ident]=="pending" and any(states[d] in {"failed","skipped"} for d in tasks[ident]["depends_on"]):
                    states[ident]="skipped";finished[ident]=now;events.append({"time":now,"event":"skipped","task_id":ident,"attempt":0});changed=True
        # Schedule ready tasks in lexical order into free workers.
        for ident in sorted(tasks):
            if len(running)>=workflow["workers"]:break
            t=tasks[ident]
            if states[ident] not in {"pending","retry_wait"}:continue
            if retry_at[ident]>now or any(states[d]!="succeeded" for d in t["depends_on"]):continue
            attempts[ident]+=1;attempt=attempts[ident];states[ident]="running"
            if first[ident] is None:first[ident]=now
            running.append((now+t["duration"],ident,attempt));events.append({"time":now,"event":"start","task_id":ident,"attempt":attempt})
        if all(s in {"succeeded","failed","skipped"} for s in states.values()):break
        future=[e for e,_,_ in running if e>now]
        future += [retry_at[i] for i,s in states.items() if s=="retry_wait" and retry_at[i]>now]
        if not future:
            raise ValueError("scheduler made no progress")
        now=min(future)
    rows=[]
    for ident in sorted(tasks):
        final=states[ident]
        rows.append({"task_id":ident,"state":final,"attempts":attempts[ident],"started_at":first[ident],"finished_at":finished[ident]})
    return {"workflow_id":workflow["workflow_id"],"status":"succeeded" if all(s=="succeeded" for s in states.values()) else "failed","finished_at":max((x for x in finished.values() if x is not None),default=0),"events":events,"tasks":rows}
