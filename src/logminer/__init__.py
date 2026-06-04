"""logminer: cluster raw logs into templates (a small, dependency-free Drain)."""
from .mask import mask_variables
from .miner import TemplateMiner, Cluster
__all__ = ["mask_variables", "TemplateMiner", "Cluster"]
__version__ = "0.1.0"
