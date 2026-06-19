"""logminer: cluster raw logs into templates (a small, dependency-free Drain)."""
from .mask import mask_variables
from .miner import TemplateMiner, Cluster, extract_parameters
__all__ = ["mask_variables", "TemplateMiner", "Cluster", "extract_parameters"]
__version__ = "0.3.0"
