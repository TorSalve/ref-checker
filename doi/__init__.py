"""
DOI Library - A Python library for interacting with DOI REST APIs

This library provides a simple interface to:
- Resolve DOIs to their target URLs
- Retrieve metadata in various formats (JSON, BibTeX, etc.)
- Query CrossRef and DataCite APIs
- Retrieve abstracts from multiple sources
- Batch process multiple DOIs with rate limiting
- Export results to JSON and CSV formats

Basic Usage:
    >>> from doi import DOI, get_doi_abstract
    >>>
    >>> # Single DOI operations
    >>> doi = DOI("10.1145/3290605.3300233")
    >>> abstract = doi.get_abstract()
    >>>
    >>> # Or use convenience functions
    >>> abstract = get_doi_abstract("10.1145/3290605.3300233")
    >>>
    >>> # Batch processing
    >>> from doi import process_dois_to_csv
    >>> dois = ["10.1145/3290605.3300233", "10.1038/nature12373"]
    >>> process_dois_to_csv(dois, "output.csv", rate_limit=1.0)

For more information, see the README.md file or visit:
https://github.com/yourusername/doi-library
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

# Core classes
from .core import DOI
from .query import DOIQuery, SemanticScholarSearch
from .batch import DOIBatch

# Enums
from .enums import APISource

# Exceptions
from .exceptions import (
    DOIError,
    DOIValidationError,
    DOIResolutionError,
    DOIMetadataError,
)

# Utility functions
from .utils import clean_text_for_csv, clean_text_for_json, clean_data_structure

# Convenience API functions
from .api import (
    resolve_doi,
    get_doi_metadata,
    get_doi_citation,
    validate_doi,
    search_dois,
    get_doi_abstract,
    process_dois_to_json,
    process_dois_to_csv,
    process_doi_string,
    process_doi_string_to_json,
    process_doi_string_to_csv,
    process_doi_file,
    process_doi_file_to_json,
    process_doi_file_to_csv,
    semantic_scholar_bulk_search,
    semantic_scholar_search_all,
)

# Define public API
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core classes
    "DOI",
    "DOIQuery",
    "SemanticScholarSearch",
    "DOIBatch",
    # Enums
    "APISource",
    # Exceptions
    "DOIError",
    "DOIValidationError",
    "DOIResolutionError",
    "DOIMetadataError",
    # Utility functions
    "clean_text_for_csv",
    "clean_text_for_json",
    "clean_data_structure",
    # Convenience API
    "resolve_doi",
    "get_doi_metadata",
    "get_doi_citation",
    "validate_doi",
    "search_dois",
    "get_doi_abstract",
    "process_dois_to_json",
    "process_dois_to_csv",
    "process_doi_string",
    "process_doi_string_to_json",
    "process_doi_string_to_csv",
    "process_doi_file",
    "process_doi_file_to_json",
    "process_doi_file_to_csv",
    "semantic_scholar_bulk_search",
    "semantic_scholar_search_all",
]
