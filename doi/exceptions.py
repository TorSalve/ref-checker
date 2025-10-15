"""
Custom exceptions for the DOI library
"""


class DOIError(Exception):
    """Base exception for DOI-related errors"""

    pass


class DOIValidationError(DOIError):
    """Raised when a DOI format is invalid"""

    pass


class DOIResolutionError(DOIError):
    """Raised when a DOI cannot be resolved"""

    pass


class DOIMetadataError(DOIError):
    """Raised when metadata cannot be retrieved"""

    pass
