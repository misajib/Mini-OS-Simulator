"""
modules/file_management.py
--------------------------
Disk file allocation logic — zero Tkinter.

Public API
----------
allocate_sequential(file_specs, total_blocks) -> FileAllocationResult
allocate_linked    (file_specs, total_blocks) -> FileAllocationResult
allocate_indexed   (file_specs, total_blocks) -> FileAllocationResult
"""
from __future__ import annotations
from dataclasses import dataclass, field
import random
@dataclass
class FileEntry:
    name:        str
    size:        int
    start_block: int | None
    blocks:      list[int]
    index_block: int | None = None
@dataclass
class FileAllocationResult:
    method:       str
    total_blocks: int
    files:        list[FileEntry]
    fat:          list[dict]
    block_map:    dict[int, str]
    free_blocks:  list[int]
    used_blocks:  int
    free_count:   int
    utilisation:  float
    log:          list[str]
# ── Helpers ───────────────────────────────────────────────────────────────────
def _pick_random(free: list[int], n: int) -> list[int]:
    if len(free) < n:
        raise ValueError(f"Not enough free blocks. Need {n}, available {len(free)}.")
    return sorted(random.sample(free, n))
def _base_result(method: str, files: list[FileEntry],
                 total: int, block_map: dict[int, str],
                 log: list[str]) -> FileAllocationResult:
    used      = len(block_map)
    free_list = [i for i in range(total) if i not in block_map]
    return FileAllocationResult(
        method=method, total_blocks=total, files=files, fat=[],
        block_map=block_map, free_blocks=free_list,
        used_blocks=used, free_count=len(free_list),
        utilisation=round(used / total * 100, 1) if total else 0.0,
        log=log,
    )
def _find_contiguous(free: list[int], n: int) -> int | None:
    sorted_free = sorted(free)
    if not sorted_free:
        return None
    run_start = sorted_free[0]
    run_len   = 1
    for i in range(1, len(sorted_free)):
        if sorted_free[i] == sorted_free[i - 1] + 1:
            run_len += 1
            if run_len >= n:
                return run_start
        else:
            run_start = sorted_free[i]
            run_len   = 1
    return run_start if run_len >= n else None
def _validate(file_specs: list, total_blocks: int):
    if total_blocks < 8 or total_blocks > 256:
        raise ValueError("Total blocks must be between 8 and 256.")
    if not file_specs:
        raise ValueError("At least one file is required.")
    for name, size in file_specs:
        if not name.strip():
            raise ValueError("File name cannot be empty.")
        if size < 1:
            raise ValueError(f"File '{name}': size must be >= 1 block.")
# ── Sequential allocation ─────────────────────────────────────────────────────
def allocate_sequential(file_specs: list[tuple[str, int]],
                         total_blocks: int) -> FileAllocationResult:
    _validate(file_specs, total_blocks)
    free_blocks = list(range(total_blocks))
    block_map: dict[int, str] = {}
    file_entries, fat_rows, log = [], [], []
    for name, size in file_specs:
        start = _find_contiguous(free_blocks, size)
        if start is None:
            log.append(f"✘ {name}: cannot find {size} contiguous blocks.")
            continue
        blocks = list(range(start, start + size))
        for b in blocks:
            block_map[b] = name
            free_blocks.remove(b)
        file_entries.append(FileEntry(name, size, start, blocks))
        fat_rows.append({"File": name, "Start": start,
                          "Length": size, "Blocks": f"{start}–{start+size-1}"})
        log.append(f"✔ {name}: blocks {start}–{start+size-1}")
    result = _base_result("Sequential", file_entries, total_blocks, block_map, log)
    result.fat = fat_rows
    return result
# ── Linked allocation ─────────────────────────────────────────────────────────
def allocate_linked(file_specs: list[tuple[str, int]],
                     total_blocks: int) -> FileAllocationResult:
    _validate(file_specs, total_blocks)
    free_blocks = list(range(total_blocks))
    block_map: dict[int, str] = {}
    file_entries, fat_rows, log = [], [], []
    for name, size in file_specs:
        if len(free_blocks) < size:
            log.append(f"✘ {name}: not enough free blocks.")
            continue
        chosen = _pick_random(free_blocks, size)
        for b in chosen:
            block_map[b] = name
            free_blocks.remove(b)
        chain_str = " -> ".join(str(b) for b in chosen) + " -> NULL"
        file_entries.append(FileEntry(name, size, chosen[0], chosen))
        fat_rows.append({"File": name, "Start": chosen[0],
                          "Blocks": str(chosen), "Chain": chain_str})
        log.append(f"✔ {name}: {chain_str}")

    result = _base_result("Linked", file_entries, total_blocks, block_map, log)
    result.fat = fat_rows
    return result
# ── Indexed allocation ────────────────────────────────────────────────────────
def allocate_indexed(file_specs: list[tuple[str, int]],
                      total_blocks: int) -> FileAllocationResult:
    _validate(file_specs, total_blocks)
    free_blocks = list(range(total_blocks))
    block_map: dict[int, str] = {}
    file_entries, fat_rows, log = [], [], []
    for name, size in file_specs:
        needed = size + 1
        if len(free_blocks) < needed:
            log.append(f"✘ {name}: need {needed} blocks ({size}+1 index).")
            continue
        idx_block = free_blocks[0]
        free_blocks.remove(idx_block)
        block_map[idx_block] = f"{name}[IDX]"
        data_blocks = _pick_random(free_blocks, size)
        for b in data_blocks:
            block_map[b] = name
            free_blocks.remove(b)
        file_entries.append(FileEntry(name, size, None, data_blocks, idx_block))
        fat_rows.append({"File": name, "Index Block": idx_block,
                          "Data Blocks": str(data_blocks), "Size": size})
        log.append(f"✔ {name}: index@{idx_block}, data={data_blocks}")
    result = _base_result("Indexed", file_entries, total_blocks, block_map, log)
    result.fat = fat_rows
    return result