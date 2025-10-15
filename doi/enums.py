"""
Enumerations for the DOI library
"""

from enum import Enum


class APISource(Enum):
    """Enum for available API sources for abstract retrieval"""

    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    DATACITE = "datacite"
    CSL_JSON = "csl_json"
    AUTO = "auto"  # Try all sources in order
