"""
Audiobook Generation Pipelines
Different generation modes and workflows
"""

from .standard_single_voice import SingleVoicePipeline
from .phoenix_peacock_dual_voice import DualVoicePipeline

__all__ = [
    "SingleVoicePipeline",
    "DualVoicePipeline"
]
