#!/usr/bin/env python3
"""
Academic Paper Reference Checker

This script provides a simple entry point to the ref_checker package.
For the actual implementation, see the ref_checker package modules:
- ref_checker.extractor: PDF text extraction and reference parsing
- ref_checker.checker: DOI validation and title-based verification
- ref_checker.reporter: Report generation (JSON and Markdown)
"""

# Import and run the main function from the package
from ref_checker.__main__ import main

if __name__ == "__main__":
    main()
