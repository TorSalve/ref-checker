"""
Academic Paper Reference Checker

A tool for extracting and verifying references from academic papers in PDF format.
Supports both DOI validation and title-based search using Semantic Scholar.
"""

from .extractor import ReferenceExtractor
from .checker import ReferenceChecker
from .reporter import ReportGenerator
from .batch import BatchProcessor

__version__ = "1.0.0"
__all__ = [
    "ReferenceExtractor",
    "ReferenceChecker",
    "ReportGenerator",
    "BatchProcessor",
]
