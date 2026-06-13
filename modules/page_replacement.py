"""
modules/page_replacement.py
---------------------------
Pure page-replacement logic — zero Tkinter.

Public API
----------
run(algorithm, reference_string, n_frames)
    algorithm: "fifo" | "lru" | "optimal"
    returns  : PageReplacementResult
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque, OrderedDict


# ─────────────────────────────────────────────────────────────────────────────
# Result type
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepState:
    reference:   int
    frames:      list[int | None]   # snapshot of frame contents after this step
    is_fault:    bool
    replaced:    int | None = None  # page that was replaced (None if no fault)


@dataclass
class PageReplacementResult:
    algorithm:        str
    reference_string: list[int]
    n_frames:         int
    steps:            list[StepState]
    page_faults:      int
    page_hits:        int
    hit_ratio:        float
    fault_ratio:      float


# ─────────────────────────────────────────────────────────────────────────────
# FIFO
# ─────────────────────────────────────────────────────────────────────────────

def _fifo(ref: list[int], n: int) -> PageReplacementResult:
    frames:  list[int | None] = [None] * n
    queue:   deque[int]       = deque()   # insertion order
    faults  = 0
    steps   = []

    for page in ref:
        if page in frames:
            steps.append(StepState(page, list(frames), False))
        else:
            faults += 1
            replaced = None
            if len(queue) == n:
                oldest   = queue.popleft()
                idx      = frames.index(oldest)
                replaced = oldest
                frames[idx] = page
            else:
                idx = frames.index(None)
                frames[idx] = page
            queue.append(page)
            steps.append(StepState(page, list(frames), True, replaced))

    total     = len(ref)
    hits      = total - faults
    return PageReplacementResult(
        algorithm="FIFO",
        reference_string=ref,
        n_frames=n,
        steps=steps,
        page_faults=faults,
        page_hits=hits,
        hit_ratio=round(hits / total, 4) if total else 0.0,
        fault_ratio=round(faults / total, 4) if total else 0.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LRU
# ─────────────────────────────────────────────────────────────────────────────

def _lru(ref: list[int], n: int) -> PageReplacementResult:
    frames: list[int | None] = [None] * n
    # ordered dict: most-recently used at END
    lru_tracker: OrderedDict[int, None] = OrderedDict()
    faults = 0
    steps  = []

    for page in ref:
        if page in frames:
            lru_tracker.move_to_end(page)
            steps.append(StepState(page, list(frames), False))
        else:
            faults += 1
            replaced = None
            if None not in frames:
                # evict least recently used (first key in OrderedDict)
                lru_page = next(iter(lru_tracker))
                lru_tracker.pop(lru_page)
                idx      = frames.index(lru_page)
                replaced = lru_page
                frames[idx] = page
            else:
                idx = frames.index(None)
                frames[idx] = page
            lru_tracker[page] = None
            steps.append(StepState(page, list(frames), True, replaced))

    total = len(ref)
    hits  = total - faults
    return PageReplacementResult(
        algorithm="LRU",
        reference_string=ref,
        n_frames=n,
        steps=steps,
        page_faults=faults,
        page_hits=hits,
        hit_ratio=round(hits / total, 4) if total else 0.0,
        fault_ratio=round(faults / total, 4) if total else 0.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Optimal
# ─────────────────────────────────────────────────────────────────────────────

def _optimal(ref: list[int], n: int) -> PageReplacementResult:
    frames: list[int | None] = [None] * n
    faults = 0
    steps  = []

    for i, page in enumerate(ref):
        if page in frames:
            steps.append(StepState(page, list(frames), False))
        else:
            faults += 1
            replaced = None
            if None not in frames:
                # Find the page used furthest in the future (or never used)
                future   = ref[i + 1:]
                farthest = -1
                victim   = None
                for fp in frames:
                    if fp not in future:
                        victim = fp
                        break
                    next_use = future.index(fp)
                    if next_use > farthest:
                        farthest = next_use
                        victim   = fp
                replaced        = victim
                idx             = frames.index(victim)
                frames[idx]     = page
            else:
                idx         = frames.index(None)
                frames[idx] = page
            steps.append(StepState(page, list(frames), True, replaced))

    total = len(ref)
    hits  = total - faults
    return PageReplacementResult(
        algorithm="Optimal",
        reference_string=ref,
        n_frames=n,
        steps=steps,
        page_faults=faults,
        page_hits=hits,
        hit_ratio=round(hits / total, 4) if total else 0.0,
        fault_ratio=round(faults / total, 4) if total else 0.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

_ALGO_MAP = {
    "fifo":    _fifo,
    "lru":     _lru,
    "optimal": _optimal,
}


def run(algorithm: str,
        reference_string: list[int],
        n_frames: int) -> PageReplacementResult:
    """
    Public dispatcher.

    Parameters
    ----------
    algorithm        : "fifo" | "lru" | "optimal"
    reference_string : list of page numbers (ints)
    n_frames         : number of physical frames
    """
    key = algorithm.lower()
    fn  = _ALGO_MAP.get(key)
    if fn is None:
        raise ValueError(f"Unknown algorithm '{algorithm}'. "
                         f"Choose from: {list(_ALGO_MAP)}")
    if not reference_string:
        raise ValueError("Reference string cannot be empty.")
    if n_frames < 1:
        raise ValueError("Frame count must be ≥ 1.")
    if n_frames > 20:
        raise ValueError("Frame count must be ≤ 20.")
    return fn(list(reference_string), n_frames)