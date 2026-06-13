"""
modules/memory_management.py
----------------------------
Pure memory allocation logic — zero Tkinter.

Public API
----------
allocate(algorithm, block_sizes, process_sizes) -> AllocationResult
paging(process_size, page_size, memory_size)    -> PagingResult

Supported algorithms: "first_fit" | "best_fit" | "worst_fit"
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math


@dataclass
class BlockState:
    block_id:      int
    block_size:    int
    allocated_to:  str | None = None
    process_size:  int        = 0
    fragmentation: int        = 0

    @property
    def is_free(self) -> bool:
        return self.allocated_to is None


@dataclass
class AllocationResult:
    blocks:              list[BlockState]
    allocations:         list[dict]
    unallocated:         list[str]
    total_internal_frag: int
    total_external_frag: int
    memory_utilisation:  float


@dataclass
class PageEntry:
    page_no:  int
    frame_no: int


@dataclass
class PagingResult:
    page_table:    list[PageEntry]
    total_pages:   int
    total_frames:  int
    used_frames:   int
    free_frames:   int
    internal_frag: int
    page_size:     int
    process_size:  int
    memory_size:   int


# ── Shared helpers ────────────────────────────────────────────────────────────

def _init_blocks(sizes: list[int]) -> list[BlockState]:
    return [BlockState(block_id=i, block_size=s) for i, s in enumerate(sizes)]


def _apply_allocations(blocks: list[BlockState],
                        processes: list[int]) -> AllocationResult:
    allocs, unalloc = [], []
    for i, ps in enumerate(processes):
        pid = f"P{i+1}"
        blk = next((b for b in blocks if b.allocated_to == pid), None)
        if blk:
            allocs.append({"pid": pid, "proc_size": ps,
                            "block_id": blk.block_id, "frag": blk.fragmentation})
        else:
            unalloc.append(pid)

    total_int_frag = sum(b.fragmentation for b in blocks if not b.is_free)
    used_memory    = sum(b.process_size  for b in blocks if not b.is_free)
    total_memory   = sum(b.block_size    for b in blocks)

    remaining_proc_sizes = [processes[int(p[1:]) - 1] for p in unalloc]
    ext_frag = 0
    if remaining_proc_sizes:
        min_need = min(remaining_proc_sizes)
        ext_frag = sum(b.block_size for b in blocks
                       if b.is_free and b.block_size < min_need)

    util = (used_memory / total_memory * 100) if total_memory > 0 else 0.0
    return AllocationResult(
        blocks=blocks,
        allocations=allocs,
        unallocated=unalloc,
        total_internal_frag=total_int_frag,
        total_external_frag=ext_frag,
        memory_utilisation=round(util, 1),
    )


# ── First Fit ─────────────────────────────────────────────────────────────────

def first_fit(block_sizes: list[int], process_sizes: list[int]) -> AllocationResult:
    blocks = _init_blocks(block_sizes)
    for i, ps in enumerate(process_sizes):
        pid = f"P{i+1}"
        for b in blocks:
            if b.is_free and b.block_size >= ps:
                b.allocated_to  = pid
                b.process_size  = ps
                b.fragmentation = b.block_size - ps
                break
    return _apply_allocations(blocks, process_sizes)


# ── Best Fit ──────────────────────────────────────────────────────────────────

def best_fit(block_sizes: list[int], process_sizes: list[int]) -> AllocationResult:
    blocks = _init_blocks(block_sizes)
    for i, ps in enumerate(process_sizes):
        pid      = f"P{i+1}"
        eligible = [b for b in blocks if b.is_free and b.block_size >= ps]
        if eligible:
            chosen = min(eligible, key=lambda b: b.block_size)
            chosen.allocated_to  = pid
            chosen.process_size  = ps
            chosen.fragmentation = chosen.block_size - ps
    return _apply_allocations(blocks, process_sizes)


# ── Worst Fit ─────────────────────────────────────────────────────────────────

def worst_fit(block_sizes: list[int], process_sizes: list[int]) -> AllocationResult:
    blocks = _init_blocks(block_sizes)
    for i, ps in enumerate(process_sizes):
        pid      = f"P{i+1}"
        eligible = [b for b in blocks if b.is_free and b.block_size >= ps]
        if eligible:
            chosen = max(eligible, key=lambda b: b.block_size)
            chosen.allocated_to  = pid
            chosen.process_size  = ps
            chosen.fragmentation = chosen.block_size - ps
    return _apply_allocations(blocks, process_sizes)


# ── Next Fit ──────────────────────────────────────────────────────────────────

def next_fit(block_sizes: list[int], process_sizes: list[int]) -> AllocationResult:
    blocks = _init_blocks(block_sizes)
    last   = 0
    n      = len(blocks)
    for i, ps in enumerate(process_sizes):
        pid   = f"P{i+1}"
        found = False
        for offset in range(n):
            idx = (last + offset) % n
            b   = blocks[idx]
            if b.is_free and b.block_size >= ps:
                b.allocated_to  = pid
                b.process_size  = ps
                b.fragmentation = b.block_size - ps
                last  = idx
                found = True
                break
    return _apply_allocations(blocks, process_sizes)


# ── Dispatcher ────────────────────────────────────────────────────────────────

_ALGO_MAP = {
    "first_fit": first_fit,
    "best_fit":  best_fit,
    "worst_fit": worst_fit,
    "next_fit":  next_fit,
}


def allocate(algorithm: str,
             block_sizes: list[int],
             process_sizes: list[int]) -> AllocationResult:
    key = algorithm.lower().replace(" ", "_")
    fn  = _ALGO_MAP.get(key)
    if fn is None:
        raise ValueError(f"Unknown algorithm '{algorithm}'. "
                         f"Choose from: {list(_ALGO_MAP)}")
    if not block_sizes:
        raise ValueError("block_sizes cannot be empty.")
    if not process_sizes:
        raise ValueError("process_sizes cannot be empty.")
    if any(s <= 0 for s in block_sizes):
        raise ValueError("All block sizes must be > 0.")
    if any(s <= 0 for s in process_sizes):
        raise ValueError("All process sizes must be > 0.")
    return fn(block_sizes, process_sizes)


# ── Paging ────────────────────────────────────────────────────────────────────

def paging(process_size: int, page_size: int, memory_size: int) -> PagingResult:
    if page_size    <= 0: raise ValueError("Page size must be > 0.")
    if process_size <= 0: raise ValueError("Process size must be > 0.")
    if memory_size  <= 0: raise ValueError("Memory size must be > 0.")

    total_pages   = math.ceil(process_size / page_size)
    total_frames  = memory_size // page_size
    used_frames   = min(total_pages, total_frames)
    free_frames   = total_frames - used_frames
    internal_frag = (total_pages * page_size) - process_size

    return PagingResult(
        page_table=[PageEntry(i, i) for i in range(used_frames)],
        total_pages=total_pages,
        total_frames=total_frames,
        used_frames=used_frames,
        free_frames=free_frames,
        internal_frag=internal_frag,
        page_size=page_size,
        process_size=process_size,
        memory_size=memory_size,
    )