"""Token-based online log clustering (simplified Drain)."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from .mask import mask_variables

WILDCARD = "<*>"


def _is_placeholder(token: str) -> bool:
    """A template slot that stands in for a variable: `<*>` or a mask like `<IP>`."""
    return len(token) > 2 and token.startswith("<") and token.endswith(">")


def extract_parameters(template: List[str], line: str) -> List[str]:
    """The raw tokens of `line` that fall at the template's variable positions
    (wildcards and mask placeholders). Empty if the lengths don't line up."""
    raw = line.split()
    if len(raw) != len(template):
        return []
    return [raw[i] for i, t in enumerate(template) if _is_placeholder(t)]


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

    def extract(self, line: str) -> Optional[Tuple[Cluster, List[str]]]:
        """Match `line` to a trained cluster and pull out its parameter values.
        Returns (cluster, params), or None if nothing matches. Read-only."""
        cluster = self.match(line)
        if cluster is None:
            return None
        return cluster, extract_parameters(cluster.template, line)

    def mine(self, lines: List[str]) -> List[Cluster]:
        for line in lines:
            self.add_log(line)
        return self.top()

    def top(self) -> List[Cluster]:
        return sorted(self.clusters, key=lambda c: -c.count)

    # --- persistence: train once, serialize, reload to classify a stream ---------

    def to_dict(self) -> Dict[str, Any]:
        """A JSON-serializable snapshot of the trained miner."""
        return {
            "threshold": self.threshold,
            "mask": self.mask,
            "next_id": self._next_id,
            "clusters": [
                {"id": c.id, "template": c.template, "count": c.count, "examples": c.examples}
                for c in self.clusters
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMiner":
        """Rebuild a miner from `to_dict()` output — ready to `match`/`extract`/`add_log`."""
        m = cls(similarity_threshold=data.get("threshold", 0.5), mask=data.get("mask", True))
        for cd in data.get("clusters", []):
            c = Cluster(id=cd["id"], template=list(cd["template"]),
                        count=cd.get("count", 0), examples=list(cd.get("examples", [])))
            m.clusters.append(c)
            m._by_len.setdefault(len(c.template), []).append(c)
        # keep new ids unique even if `next_id` was stale or absent
        m._next_id = max(int(data.get("next_id", 0)),
                         (max(c.id for c in m.clusters) + 1) if m.clusters else 0)
        return m

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls, text: str) -> "TemplateMiner":
        return cls.from_dict(json.loads(text))
