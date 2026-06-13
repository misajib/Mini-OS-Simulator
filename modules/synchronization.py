"""
modules/synchronization.py
--------------------------
Producer-Consumer simulation logic — zero Tkinter.
Driven by the GUI layer calling tick() repeatedly.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


class AgentState(Enum):
    IDLE      = auto()
    PRODUCING = auto()
    WAITING   = auto()
    CONSUMING = auto()
    BLOCKED   = auto()


@dataclass
class SimState:
    tick:            int
    buffer:          list[int | None]
    buffer_size:     int
    semaphore_empty: int
    semaphore_full:  int
    mutex:           bool
    producer_state:  AgentState
    consumer_state:  AgentState
    produced_count:  int
    consumed_count:  int
    log:             list[str]


class ProducerConsumerSim:
    """Bounded-buffer Producer-Consumer simulation (discrete ticks)."""

    def __init__(self, buffer_size: int = 5):
        self.buffer_size = max(2, min(16, int(buffer_size)))
        self._reset_state()

    def _reset_state(self):
        self._buffer     = [None] * self.buffer_size
        self._head = self._tail = self._count = 0
        self._sem_empty  = self.buffer_size
        self._sem_full   = 0
        self._mutex      = False
        self._prod_state = AgentState.IDLE
        self._cons_state = AgentState.IDLE
        self._produced   = self._consumed = 0
        self._tick       = 0
        self._log: list[str] = []
        self._running    = False
        self._item_ctr   = 1
        self._prod_phase = self._cons_phase = 0

    def start(self):
        self._running    = True
        self._prod_phase = 0
        self._cons_phase = 0
        self._log_event("Simulation started.")

    def stop(self):
        self._running    = False
        self._prod_state = AgentState.IDLE
        self._cons_state = AgentState.IDLE
        self._log_event("Simulation stopped.")

    def reset(self):
        self._reset_state()
        self._log_event("Simulation reset.")

    def tick(self) -> SimState:
        if self._running:
            self._tick += 1
            self._step_producer()
            self._step_consumer()
        return self._snapshot()

    def get_state(self) -> SimState:
        return self._snapshot()

    # ── Producer ──────────────────────────────────────────────────────────────

    def _step_producer(self):
        if self._prod_phase == 0:
            if self._sem_empty > 0:
                self._prod_state = AgentState.PRODUCING
                self._prod_phase = 1
                self._log_event(f"[Producer] Producing item #{self._item_ctr}…")
            else:
                self._prod_state = AgentState.BLOCKED
                self._log_event("[Producer] BLOCKED — buffer full.")
        elif self._prod_phase == 1:
            self._prod_phase = 2
            self._prod_state = AgentState.WAITING
        elif self._prod_phase == 2:
            if not self._mutex:
                self._mutex     = True
                item            = self._item_ctr
                self._buffer[self._head] = item
                self._head      = (self._head + 1) % self.buffer_size
                self._count    += 1
                self._sem_empty -= 1
                self._sem_full  += 1
                self._produced  += 1
                self._item_ctr  += 1
                self._mutex     = False
                self._prod_state = AgentState.IDLE
                self._prod_phase = 0
                self._log_event(f"[Producer] ✔ Produced item {item}. "
                                f"Buffer: {self._count}/{self.buffer_size}")
            else:
                self._prod_state = AgentState.WAITING
                self._log_event("[Producer] Waiting for mutex…")

    # ── Consumer ──────────────────────────────────────────────────────────────

    def _step_consumer(self):
        if self._cons_phase == 0:
            if self._sem_full > 0:
                self._cons_state = AgentState.CONSUMING
                self._cons_phase = 1
                self._log_event("[Consumer] Consuming item…")
            else:
                self._cons_state = AgentState.BLOCKED
                self._log_event("[Consumer] BLOCKED — buffer empty.")
        elif self._cons_phase == 1:
            self._cons_phase = 2
            self._cons_state = AgentState.WAITING
        elif self._cons_phase == 2:
            if not self._mutex:
                self._mutex     = True
                item            = self._buffer[self._tail]
                self._buffer[self._tail] = None
                self._tail      = (self._tail + 1) % self.buffer_size
                self._count    -= 1
                self._sem_full  -= 1
                self._sem_empty += 1
                self._consumed  += 1
                self._mutex     = False
                self._cons_state = AgentState.IDLE
                self._cons_phase = 0
                self._log_event(f"[Consumer] ✔ Consumed item {item}. "
                                f"Buffer: {self._count}/{self.buffer_size}")
            else:
                self._cons_state = AgentState.WAITING
                self._log_event("[Consumer] Waiting for mutex…")

    def _log_event(self, msg: str):
        self._log.append(msg)
        if len(self._log) > 200:
            self._log = self._log[-200:]

    def _snapshot(self) -> SimState:
        return SimState(
            tick=self._tick,
            buffer=list(self._buffer),
            buffer_size=self.buffer_size,
            semaphore_empty=self._sem_empty,
            semaphore_full=self._sem_full,
            mutex=self._mutex,
            producer_state=self._prod_state,
            consumer_state=self._cons_state,
            produced_count=self._produced,
            consumed_count=self._consumed,
            log=list(self._log),
        )