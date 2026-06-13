"""
modules/deadlock.py
-------------------
Banker's Algorithm — pure logic, zero Tkinter.

Public API
----------
bankers(available, allocation, maximum) -> BankersResult
"""
from __future__ import annotations
from dataclasses import dataclass
@dataclass
class BankersResult:
    n_processes:   int
    n_resources:   int
    available:     list[int]
    allocation:    list[list[int]]
    maximum:       list[list[int]]
    need:          list[list[int]]
    is_safe:       bool
    safe_sequence: list[int]
    steps:         list[str]
def bankers(available:  list[int],
            allocation: list[list[int]],
            maximum:    list[list[int]]) -> BankersResult:
    n = len(allocation)
    if n == 0:
        raise ValueError("At least one process required.")
    m = len(available)
    if m == 0:
        raise ValueError("At least one resource type required.")
    for i in range(n):
        if len(allocation[i]) != m:
            raise ValueError(f"Allocation row {i}: expected {m} values.")
        if len(maximum[i]) != m:
            raise ValueError(f"Maximum row {i}: expected {m} values.")
        for j in range(m):
            if allocation[i][j] < 0:
                raise ValueError(f"Allocation[{i}][{j}] cannot be negative.")
            if maximum[i][j] < 0:
                raise ValueError(f"Maximum[{i}][{j}] cannot be negative.")
            if allocation[i][j] > maximum[i][j]:
                raise ValueError(
                    f"Allocation[{i}][{j}] ({allocation[i][j]}) exceeds "
                    f"Maximum[{i}][{j}] ({maximum[i][j]}).")
    need = [[maximum[i][j] - allocation[i][j] for j in range(m)]
            for i in range(n)]
    work   = list(available)
    finish = [False] * n
    safe_seq: list[int] = []
    steps:    list[str] = []
    steps.append(f"Initial Work (Available) = {work}")
    steps.append("Need matrix computed.")
    for _ in range(n * n + 1):
        if len(safe_seq) >= n:
            break
        found = False
        for i in range(n):
            if finish[i]:
                continue
            if all(need[i][j] <= work[j] for j in range(m)):
                steps.append(
                    f"Step {len(safe_seq)+1}: P{i} — "
                    f"Need={need[i]} <= Work={work}  -> ALLOCATED")
                finish[i] = True
                for j in range(m):
                    work[j] += allocation[i][j]
                safe_seq.append(i)
                steps.append(f"  Work updated to {work}")
                found = True
        if not found:
            break
    is_safe = all(finish)
    if is_safe:
        seq_str = " -> ".join(f"P{i}" for i in safe_seq)
        steps.append(f"\n✔ SAFE STATE — Safe sequence: {seq_str}")
    else:
        unfinished = [f"P{i}" for i in range(n) if not finish[i]]
        steps.append("\n✘ UNSAFE STATE — Deadlock possible.")
        steps.append(f"  Processes that cannot complete: {unfinished}")
    return BankersResult(
        n_processes=n, n_resources=m,
        available=list(available),
        allocation=[list(row) for row in allocation],
        maximum=[list(row) for row in maximum],
        need=need,is_safe=is_safe,
        safe_sequence=safe_seq,steps=steps,)