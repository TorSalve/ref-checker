"""
Batch processing module for checking multiple PDFs.

This module provides functionality to process multiple PDF files in a folder,
generate individual reports for each, and create collective summary reports.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .extractor import ReferenceExtractor
from .checker import ReferenceChecker
from .reporter import ReportGenerator


class BatchProcessor:
    """Process multiple PDFs and generate collective reports"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 10,
        verbose: bool = True,
    ):
        """
        Initialize the batch processor

        Args:
            api_key: Optional Semantic Scholar API key
            timeout: Timeout for API requests in seconds
            verbose: Whether to print progress messages
        """
        self.api_key = api_key
        self.timeout = timeout
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Process a single PDF and generate its reports.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output files

        Returns:
            Dictionary with processing results and statistics
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"Processing: {pdf_path.name}")
            print(f"{'='*70}")

        try:
            # Extract references
            extractor = ReferenceExtractor(str(pdf_path))
            references = extractor.extract_references()

            if not references:
                if self.verbose:
                    print(f"  ✗ No references found in {pdf_path.name}")
                return {
                    "pdf": pdf_path.name,
                    "status": "error",
                    "error": "No references found",
                    "stats": {
                        "total": 0,
                        "verified": 0,
                        "errors": 0,
                        "success_rate": 0.0,
                    },
                }

            if self.verbose:
                print(f"  ✓ Found {len(references)} reference(s)")

            # Check references
            checker = ReferenceChecker(
                timeout=self.timeout, semantic_scholar_api_key=self.api_key
            )
            checker.check_references(references, verbose=False)
            results = checker.results  # List of reference dicts

            # Calculate statistics
            total = len(results)
            verified = sum(1 for ref in results if ref.get("exists"))
            errors = sum(1 for ref in results if ref.get("error"))
            success_rate = (verified / total * 100) if total > 0 else 0.0

            # Get detailed stats from checker
            report = checker.generate_report()

            if self.verbose:
                print(f"  ✓ Verified: {verified}/{total} ({success_rate:.1f}%)")

            # Generate output filenames
            base_name = pdf_path.stem
            json_file = output_dir / f"{base_name}.json"
            md_file = output_dir / f"{base_name}.md"

            # Generate and save reports
            reporter = ReportGenerator(results)
            reporter.save_json(str(json_file))
            reporter.save_markdown(str(md_file))

            if self.verbose:
                print(f"  ✓ Reports saved: {json_file.name}, {md_file.name}")

            return {
                "pdf": pdf_path.name,
                "status": "success",
                "stats": {
                    "total": total,
                    "verified": verified,
                    "errors": errors,
                    "success_rate": success_rate,
                    "doi_count": report.get("doi_valid", 0),
                    "title_count": report.get("title_valid", 0),
                },
                "json_report": str(json_file),
                "md_report": str(md_file),
            }

        except Exception as e:
            if self.verbose:
                print(f"  ✗ Error processing {pdf_path.name}: {e}")
                import traceback

                traceback.print_exc()

            return {
                "pdf": pdf_path.name,
                "status": "error",
                "error": str(e),
                "stats": {
                    "total": 0,
                    "verified": 0,
                    "errors": 0,
                    "success_rate": 0.0,
                },
            }

    def process_folder(
        self,
        folder: Path,
        output_dir: Optional[Path] = None,
        pattern: str = "*.pdf",
    ) -> List[Dict[str, Any]]:
        """
        Process all PDFs in a folder

        Args:
            folder: Folder containing PDF files
            output_dir: Output directory (defaults to same as input folder)
            pattern: Glob pattern for PDF files

        Returns:
            List of processing results for each PDF
        """
        # Set output directory
        if output_dir is None:
            output_dir = folder
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all PDF files
        pdf_files = sorted(folder.glob(pattern))

        if not pdf_files:
            raise ValueError(
                f"No PDF files found in '{folder}' matching pattern '{pattern}'"
            )

        if self.verbose:
            api_key_status = (
                "✓ Using Semantic Scholar API key"
                if self.api_key
                else "⚠ No API key - using public rate limits"
            )

            print(f"\n{'='*70}")
            print(f"BATCH REFERENCE CHECKER")
            print(f"{'='*70}")
            print(f"Input folder: {folder}")
            print(f"Output folder: {output_dir}")
            print(f"PDF files found: {len(pdf_files)}")
            print(f"{api_key_status}")
            print(f"{'='*70}")

        # Process each PDF
        self.results = []
        for pdf_file in pdf_files:
            result = self.process_pdf(pdf_file, output_dir)
            self.results.append(result)

        # Generate collective report
        self.generate_collective_report(output_dir)

        return self.results

    def generate_collective_report(self, output_dir: Path) -> None:
        """
        Generate a collective summary report for all processed PDFs.

        Args:
            output_dir: Directory for output files
        """
        # Calculate overall statistics
        total_pdfs = len(self.results)
        successful_pdfs = sum(1 for r in self.results if r["status"] == "success")
        failed_pdfs = total_pdfs - successful_pdfs

        total_refs = sum(r["stats"]["total"] for r in self.results)
        total_verified = sum(r["stats"]["verified"] for r in self.results)
        total_errors = sum(r["stats"]["errors"] for r in self.results)
        overall_success_rate = (
            (total_verified / total_refs * 100) if total_refs > 0 else 0.0
        )

        # Generate markdown report
        md_lines = [
            "# Batch Reference Check Report",
            "",
            f"**Generated:** {Path.cwd()}",
            "",
            "## Overall Summary",
            "",
            f"- **PDFs Processed:** {total_pdfs}",
            f"- **Successfully Processed:** {successful_pdfs}",
            f"- **Failed:** {failed_pdfs}",
            f"- **Total References:** {total_refs}",
            f"- **Verified References:** {total_verified}",
            f"- **Failed References:** {total_errors}",
            f"- **Overall Success Rate:** {overall_success_rate:.1f}%",
            "",
            "## Individual PDF Results",
            "",
        ]

        # Sort results by success rate (descending)
        sorted_results = sorted(
            self.results, key=lambda r: r["stats"]["success_rate"], reverse=True
        )

        # Add table
        md_lines.extend(
            [
                "| PDF | Status | References | Verified | Success Rate |",
                "|-----|--------|------------|----------|--------------|",
            ]
        )

        for result in sorted_results:
            status_icon = "✓" if result["status"] == "success" else "✗"
            stats = result["stats"]

            if result["status"] == "success":
                row = (
                    f"| {result['pdf']} | {status_icon} | {stats['total']} | "
                    f"{stats['verified']} | {stats['success_rate']:.1f}% |"
                )
            else:
                error = result.get("error", "Unknown error")
                row = f"| {result['pdf']} | {status_icon} | - | - | Error: {error} |"

            md_lines.append(row)

        md_lines.extend(
            [
                "",
                "## Detailed Results by PDF",
                "",
            ]
        )

        # Add detailed sections for each PDF
        for result in sorted_results:
            md_lines.extend(
                [
                    f"### {result['pdf']}",
                    "",
                ]
            )

            if result["status"] == "success":
                stats = result["stats"]
                json_name = Path(result["json_report"]).name
                md_name = Path(result["md_report"]).name
                md_lines.extend(
                    [
                        f"- **Total References:** {stats['total']}",
                        f"- **Verified:** {stats['verified']} ({stats['success_rate']:.1f}%)",
                        f"- **Errors:** {stats['errors']}",
                        f"- **DOIs Verified:** {stats.get('doi_count', 0)}",
                        f"- **Titles Verified:** {stats.get('title_count', 0)}",
                        f"- **Reports:** [{json_name}]({json_name}), [{md_name}]({md_name})",
                        "",
                    ]
                )
            else:
                md_lines.extend(
                    [
                        f"- **Status:** Failed",
                        f"- **Error:** {result.get('error', 'Unknown error')}",
                        "",
                    ]
                )

        # Save collective report
        collective_md = output_dir / "collective_report.md"
        with open(collective_md, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        # Save collective JSON
        collective_json = output_dir / "collective_report.json"
        with open(collective_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": {
                        "total_pdfs": total_pdfs,
                        "successful_pdfs": successful_pdfs,
                        "failed_pdfs": failed_pdfs,
                        "total_references": total_refs,
                        "verified_references": total_verified,
                        "failed_references": total_errors,
                        "overall_success_rate": overall_success_rate,
                    },
                    "results": self.results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        if self.verbose:
            print(f"\n{'='*70}")
            print("COLLECTIVE REPORT GENERATED")
            print(f"{'='*70}")
            print(f"✓ Markdown report: {collective_md}")
            print(f"✓ JSON report: {collective_json}")

    def print_summary(self) -> None:
        """Print a summary of batch processing results"""
        if not self.results:
            print("No results to summarize")
            return

        successful = sum(1 for r in self.results if r["status"] == "success")
        print(f"\n{'='*70}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Total PDFs: {len(self.results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(self.results) - successful}")
        print(f"{'='*70}\n")
