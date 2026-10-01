"""Core finite abstract rewriting system utilities."""

from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations
from typing import Iterable


class FiniteARS:
    """Finite ARS represented by a finite state set and directed rewrite edges."""

    def __init__(self, states: Iterable[str], edges: Iterable[tuple[str, str]]) -> None:
        state_list = list(states)
        if not state_list:
            raise ValueError("states must be non-empty")
        if len(set(state_list)) != len(state_list):
            raise ValueError("states must be unique")
        if any(not isinstance(state, str) for state in state_list):
            raise ValueError("all states must be strings")

        self._states = tuple(state_list)
        self._state_set = set(self._states)
        adjacency: dict[str, set[str]] = defaultdict(set)
        edge_set: set[tuple[str, str]] = set()

        for src, dst in edges:
            if src not in self._state_set or dst not in self._state_set:
                raise ValueError(f"edge endpoint not declared in states: ({src}, {dst})")
            edge_set.add((src, dst))
            adjacency[src].add(dst)

        self._edges = tuple(sorted(edge_set))
        self._adjacency = {state: frozenset(adjacency[state]) for state in self._states}

    @property
    def states(self) -> tuple[str, ...]:
        return self._states

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        return self._edges

    def successors(self, state: str) -> frozenset[str]:
        self._validate_state(state)
        return self._adjacency[state]

    def reachable_from(self, state: str) -> set[str]:
        self._validate_state(state)
        seen: set[str] = {state}
        queue: deque[str] = deque([state])
        while queue:
            current = queue.popleft()
            for nxt in self._adjacency[current]:
                if nxt in seen:
                    continue
                seen.add(nxt)
                queue.append(nxt)
        return seen

    def is_normal_form(self, state: str) -> bool:
        self._validate_state(state)
        return len(self._adjacency[state]) == 0

    def normal_forms(self) -> set[str]:
        return {state for state in self._states if self.is_normal_form(state)}

    def reachable_normal_forms(self, state: str) -> set[str]:
        return {node for node in self.reachable_from(state) if self.is_normal_form(node)}

    def joinable(self, left: str, right: str) -> bool:
        self._validate_state(left)
        self._validate_state(right)
        return bool(self.reachable_from(left) & self.reachable_from(right))

    def local_peaks(self) -> set[tuple[str, str, str]]:
        peaks: set[tuple[str, str, str]] = set()
        for source in self._states:
            succs = sorted(self._adjacency[source])
            for left, right in combinations(succs, 2):
                peaks.add((source, left, right))
        return peaks

    def is_terminating(self) -> bool:
        # Kahn's algorithm avoids a recursion limit on long terminating chains.
        indegree = dict.fromkeys(self._states, 0)
        for _, target in self._edges:
            indegree[target] += 1
        queue = deque(state for state in self._states if indegree[state] == 0)
        removed = 0
        while queue:
            source = queue.popleft()
            removed += 1
            for target in self._adjacency[source]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        return removed == len(self._states)

    def is_locally_confluent(self) -> bool:
        for _, left, right in self.local_peaks():
            if not self.joinable(left, right):
                return False
        return True

    def is_confluent(self) -> bool:
        for state in self._states:
            reachable = sorted(self.reachable_from(state))
            for left, right in combinations(reachable, 2):
                if not self.joinable(left, right):
                    return False
        return True

    def has_unique_reachable_normal_forms(self) -> bool:
        for state in self._states:
            if len(self.reachable_normal_forms(state)) > 1:
                return False
        return True

    def _validate_state(self, state: str) -> None:
        if state not in self._state_set:
            raise KeyError(f"unknown state: {state}")
