#!/usr/bin/env python3
"""
Command-line interface for the reference checker.

This module provides the main entry point for the CLI tool.
Supports both single PDF processing and batch folder processing.
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from .extractor import ReferenceExtractor
from .checker import ReferenceChecker
from .reporter import ReportGenerator
from .batch import BatchProcessor


def main():
    """Main entry point for the reference checker CLI"""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Extract and verify references from academic paper PDFs (single or batch)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single PDF mode
  %(prog)s paper.pdf
  %(prog)s paper.pdf -o results.json -m report.md
  %(prog)s paper.pdf --api-key YOUR_KEY --quiet
  
  # Batch mode (folder)
  %(prog)s papers/
  %(prog)s papers/ -o reports/
  %(prog)s papers/ --pattern "*2023*.pdf"
  %(prog)s papers/ --batch --api-key YOUR_KEY
        """,
    )
    parser.add_argument("path", help="Path to a PDF file or folder containing PDFs")
    parser.add_argument(
        "-o",
        "--output",
        help="Output file/directory: JSON file for single PDF, directory for batch mode",
        default=None,
    )
    parser.add_argument(
        "-m",
        "--markdown",
        help="Output markdown file (single PDF mode only)",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=10,
        help="Timeout for API requests in seconds (default: 10)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode - minimal output",
    )
    parser.add_argument(
        "--api-key",
        help="Semantic Scholar API key for higher rate limits",
        default=None,
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Force batch mode (process folder). Auto-detected if path is a directory.",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.pdf",
        help="Glob pattern for PDF files in batch mode (default: *.pdf)",
    )

    args = parser.parse_args()

    # Convert path to Path object
    path = Path(args.path)

    # Validate path exists
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        sys.exit(1)

    # Determine mode: single PDF or batch folder
    is_batch_mode = path.is_dir() or args.batch

    if args.batch and not path.is_dir():
        print(
            f"Error: --batch flag requires a directory, but '{path}' is not a directory"
        )
        sys.exit(1)

    # Get API key from command line or environment variable
    api_key = args.api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key == "your_api_key_here":
        api_key = None

    try:
        if is_batch_mode:
            # ============================================
            # BATCH MODE: Process entire folder
            # ============================================
            run_batch_mode(path, args, api_key)
        else:
            # ============================================
            # SINGLE MODE: Process one PDF
            # ============================================
            run_single_mode(path, args, api_key)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def run_single_mode(pdf_path: Path, args, api_key: str):
    """Run single PDF processing mode"""
    # Extract references
    print(f"Reading PDF: {pdf_path}")
    extractor = ReferenceExtractor(str(pdf_path))
    references = extractor.extract_references()

    if not references:
        print("\n⚠ No references found in the document.")
        print("This could mean:")
        print("  - The references section wasn't recognized")
        print("  - The PDF text extraction failed")
        sys.exit(1)

    # Count references with DOIs vs titles
    doi_count = sum(1 for ref in references if ref.get("doi"))
    title_count = sum(
        1 for ref in references if ref.get("title") and not ref.get("doi")
    )

    print(f"✓ Found {len(references)} reference(s)")
    print(f"  - {doi_count} with DOIs")
    print(f"  - {title_count} with titles (no DOI)")
    print(
        f"  - {len(references) - doi_count - title_count} without DOI or extractable title"
    )

    # Show API key status
    if api_key:
        print(f"✓ Using Semantic Scholar API key")
    else:
        print(f"⚠ No Semantic Scholar API key found - using public rate limits")
        print(
            f"  Tip: Set SEMANTIC_SCHOLAR_API_KEY in .env file for higher rate limits"
        )

    # Check references
    checker = ReferenceChecker(timeout=args.timeout, semantic_scholar_api_key=api_key)
    results = checker.check_references(references, verbose=not args.quiet)

    # Print summary
    checker.print_report()

    # Generate and save reports if requested
    reporter = ReportGenerator(results)

    if args.output:
        reporter.save_json(args.output)
        print(f"✓ Detailed results saved to: {args.output}")

    if args.markdown:
        reporter.save_markdown(args.markdown)
        print(f"✓ Markdown report saved to: {args.markdown}")


def run_batch_mode(folder: Path, args, api_key: str):
    """Run batch folder processing mode"""
    output_dir = Path(args.output) if args.output else folder

    # Create batch processor
    processor = BatchProcessor(
        api_key=api_key, timeout=args.timeout, verbose=not args.quiet
    )

    # Process all PDFs in folder
    processor.process_folder(folder=folder, output_dir=output_dir, pattern=args.pattern)

    # Print summary
    if not args.quiet:
        processor.print_summary()


if __name__ == "__main__":
    main()
