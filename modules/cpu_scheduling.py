"""
modules/cpu_scheduling.py
-------------------------
Pure CPU scheduling logic — zero Tkinter.

Public API
----------
Process          — process container
fcfs             — First Come First Serve
sjf              — Shortest Job First (Non-Preemptive)
priority_sched   — Priority Scheduling (Non-Preemptive)
round_robin      — Round Robin

Every function:
    fn(processes: list[Process | dict], **kwargs)
    -> (results: list[dict], gantt: list[tuple], avg_wt: float, avg_tat: float)

results dict keys : pid, at, bt, priority, ct, tat, wt, rt
gantt  tuple      : (pid, start, end)
"""
from __future__ import annotations
class Process:
    __slots__ = ("pid", "arrival", "burst", "priority")
    def __init__(self, pid: str, arrival: int, burst: int, priority: int = 0):
        self.pid      = str(pid)
        self.arrival  = int(arrival)
        self.burst    = int(burst)
        self.priority = int(priority)
    def to_dict(self) -> dict:
        return {"pid": self.pid, "at": self.arrival,
                "bt": self.burst, "priority": self.priority}
    def __repr__(self):
        return (f"Process(pid={self.pid!r}, arrival={self.arrival}, "
                f"burst={self.burst}, priority={self.priority})")
# ── Helpers ───────────────────────────────────────────────────────────────────
def _normalise(processes: list) -> list[dict]:
    result = []
    for p in processes:
        if isinstance(p, Process):
            result.append(p.to_dict())
        elif isinstance(p, dict):
            result.append({
                "pid":      str(p.get("pid", "?")),
                "at":       int(p.get("at",  p.get("arrival",  0))),
                "bt":       int(p.get("bt",  p.get("burst",    1))),
                "priority": int(p.get("priority", 0)),
            })
        else:
            raise TypeError(f"Expected Process or dict, got {type(p)}")
    return result
def _make_result(d: dict, ct: int, rt: int) -> dict:
    tat = ct - d["at"]
    wt  = tat - d["bt"]
    return {
        "pid":      d["pid"],"at":       d["at"],
        "bt":       d["bt"], "priority": d["priority"],
        "ct":       ct,"tat":      max(tat, 0),
        "wt":       max(wt,  0), "rt":       max(rt,  0),}
def _averages(results: list[dict]) -> tuple[float, float]:
    n = len(results)
    if n == 0:
        return 0.0, 0.0
    return (round(sum(r["wt"]  for r in results) / n, 2),
            round(sum(r["tat"] for r in results) / n, 2))

def cpu_util(results: list[dict], gantt: list[tuple]) -> float:
    if not gantt:
        return 0.0
    total_burst = sum(r["bt"] for r in results)
    span = gantt[-1][2] - gantt[0][1]
    return round((total_burst / span * 100) if span > 0 else 100.0, 1)
# ── FCFS ──────────────────────────────────────────────────────────────────────
def fcfs(processes: list) -> tuple:
    ps = sorted(_normalise(processes), key=lambda x: (x["at"], x["pid"]))
    t, gantt, results = 0, [], []
    for d in ps:
        if t < d["at"]:
            t = d["at"]
        rt = t - d["at"]
        gantt.append((d["pid"], t, t + d["bt"]))
        t += d["bt"]
        results.append(_make_result(d, t, rt))
    avg_wt, avg_tat = _averages(results)
    return results, gantt, avg_wt, avg_tat
# ── SJF (Non-Preemptive) ──────────────────────────────────────────────────────
def sjf(processes: list) -> tuple:
    ps   = _normalise(processes)
    done = set()
    t, gantt, results = 0, [], []
    while len(done) < len(ps):
        available = [d for d in ps if d["pid"] not in done and d["at"] <= t]
        if not available:
            t = min(d["at"] for d in ps if d["pid"] not in done)
            continue
        chosen = min(available, key=lambda x: (x["bt"], x["at"], x["pid"]))
        rt = t - chosen["at"]
        gantt.append((chosen["pid"], t, t + chosen["bt"]))
        t += chosen["bt"]
        done.add(chosen["pid"])
        results.append(_make_result(chosen, t, rt))
    avg_wt, avg_tat = _averages(results)
    return results, gantt, avg_wt, avg_tat
# ── Priority (Non-Preemptive) ─────────────────────────────────────────────────
def priority_sched(processes: list) -> tuple:
    """Lower priority number = higher priority."""
    ps   = _normalise(processes)
    done = set()
    t, gantt, results = 0, [], []
    while len(done) < len(ps):
        available = [d for d in ps if d["pid"] not in done and d["at"] <= t]
        if not available:
            t = min(d["at"] for d in ps if d["pid"] not in done)
            continue
        chosen = min(available, key=lambda x: (x["priority"], x["at"], x["pid"]))
        rt = t - chosen["at"]
        gantt.append((chosen["pid"], t, t + chosen["bt"]))
        t += chosen["bt"]
        done.add(chosen["pid"])
        results.append(_make_result(chosen, t, rt))
    avg_wt, avg_tat = _averages(results)
    return results, gantt, avg_wt, avg_tat
# ── Round Robin ───────────────────────────────────────────────────────────────
def round_robin(processes: list, quantum: int = 2) -> tuple:
    quantum = max(1, int(quantum))
    ps      = sorted(_normalise(processes), key=lambda x: x["at"])
    n       = len(ps)
    ps_map  = {d["pid"]: d for d in ps}

    remaining = {d["pid"]: d["bt"]  for d in ps}
    first_run = {d["pid"]: None     for d in ps}
    done_set, queue, queued = set(), [], set()
    gantt, results, t = [], [], 0

    for d in ps:
        if d["at"] <= 0:
            queue.append(d["pid"])
            queued.add(d["pid"])

    while len(done_set) < n:
        if not queue:
            pending = [d for d in ps
                       if d["pid"] not in done_set and d["pid"] not in queued]
            if not pending:
                break
            t = min(d["at"] for d in pending)
            for d in ps:
                if d["pid"] not in queued and d["at"] <= t:
                    queue.append(d["pid"])
                    queued.add(d["pid"])
            continue

        pid = queue.pop(0)
        d   = ps_map[pid]
        if first_run[pid] is None:
            first_run[pid] = t
        run = min(quantum, remaining[pid])
        gantt.append((pid, t, t + run))
        t              += run
        remaining[pid] -= run

        for od in ps:
            if od["pid"] not in queued and od["at"] <= t:
                queue.append(od["pid"])
                queued.add(od["pid"])

        if remaining[pid] == 0:
            done_set.add(pid)
            rt = first_run[pid] - d["at"]
            results.append(_make_result(d, t, rt))
        else:
            queue.append(pid)
    avg_wt, avg_tat = _averages(results)
    return results, gantt, avg_wt, avg_tat