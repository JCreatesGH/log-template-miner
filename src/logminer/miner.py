"""Token-based online log clustering (simplified Drain)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .mask import mask_variables

WILDCARD = "<*>"


@dataclass
class Cluster:
    id: int
    template: List[str]
    count: int = 0
    examples: List[str] = field(default_factory=list)

    def template_str(self) -> str:
        return " ".join(self.template)


def _similarity(a: List[str], b: List[str]) -> float:
    """Fraction of positions whose tokens match (ignoring existing wildcards)."""
    if len(a) != len(b):
        return 0.0
    if not a:
        return 1.0
    same = sum(1 for x, y in zip(a, b) if x == y or x == WILDCARD)
    return same / len(a)


class TemplateMiner:
    def __init__(self, similarity_threshold: float = 0.5, mask: bool = True) -> None:
        self.threshold = similarity_threshold
        self.mask = mask
        self.clusters: List[Cluster] = []
        self._by_len: Dict[int, List[Cluster]] = {}
        self._next_id = 0

    def _tokens(self, line: str) -> List[str]:
        return (mask_variables(line) if self.mask else line).split()

    def add_log(self, line: str) -> Cluster:
        tokens = self._tokens(line)
        bucket = self._by_len.setdefault(len(tokens), [])
        best: Optional[Cluster] = None
        best_sim = 0.0
        for c in bucket:
            sim = _similarity(c.template, tokens)
            if sim > best_sim:
                best_sim, best = sim, c
        if best is not None and best_sim >= self.threshold:
            # merge: positions that differ become wildcards
            best.template = [t if t == tok else WILDCARD
                             for t, tok in zip(best.template, tokens)]
            best.count += 1
            if len(best.examples) < 5:
                best.examples.append(line)
            return best
        cluster = Cluster(id=self._next_id, template=list(tokens), count=1, examples=[line])
        self._next_id += 1
        self.clusters.append(cluster)
        bucket.append(cluster)
        return cluster

    def match(self, line: str) -> Optional[Cluster]:
        """Return the cluster `line` would join — without mutating any state.

        Useful for classifying new lines against an already-trained miner.
        """
        tokens = self._tokens(line)
        best: Optional[Cluster] = None
        best_sim = 0.0
        for c in self._by_len.get(len(tokens), []):
            sim = _similarity(c.template, tokens)
            if sim > best_sim:
                best_sim, best = sim, c
        return best if best is not None and best_sim >= self.threshold else None

    def mine(self, lines: List[str]) -> List[Cluster]:
        for line in lines:
            self.add_log(line)
        return self.top()

    def top(self) -> List[Cluster]:
        return sorted(self.clusters, key=lambda c: -c.count)
