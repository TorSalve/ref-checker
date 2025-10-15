"""
Report generation for reference checking results.

This module handles JSON and Markdown report generation,
grouping references by verification status and confidence level.
"""

import json
from typing import List, Dict, Optional


class ReportGenerator:
    """Generate reports from reference checking results"""

    def __init__(self, results: List[Dict]):
        """
        Initialize the report generator

        Args:
            results: List of reference check results
        """
        self.results = results

    @staticmethod
    def _get_reference_title(ref: Dict) -> str:
        """
        Extract the best available title from a reference

        Args:
            ref: Reference dictionary

        Returns:
            Title string, or "Unknown Title" if none found
        """
        return ref.get("matched_title") or ref.get("title", "Unknown Title")

    @staticmethod
    def _get_search_method(ref: Dict) -> Optional[str]:
        """
        Get human-readable search method from reference

        Args:
            ref: Reference dictionary

        Returns:
            Search method string or None
        """
        if ref.get("search_method"):
            return (
                "DOI lookup"
                if ref["search_method"] in ["doi", "doi_batch"]
                else "Title search"
            )
        return None

    @staticmethod
    def _render_original_reference(ref: Dict) -> List[str]:
        """
        Render the original parsed reference section

        Args:
            ref: Reference dictionary

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append("##### Original Reference (Parsed from PDF)\n")

        if ref.get("raw_text"):
            lines.append(f"**Parsed Reference**: `{ref['raw_text']}`\n")
        if ref.get("title"):
            lines.append(f"**Title**: {ref['title']}  ")
        if ref.get("authors"):
            lines.append(f"**Authors**: {ref['authors']}  ")
        if ref.get("year"):
            lines.append(f"**Year**: {ref['year']}  ")
        if ref.get("doi"):
            lines.append(f"**DOI**: [{ref['doi']}](https://doi.org/{ref['doi']})  ")
        if ref.get("publisher"):
            lines.append(f"**Publisher**: {ref['publisher']}  ")
        if ref.get("journal"):
            lines.append(f"**Journal**: {ref['journal']}  ")
        if ref.get("volume"):
            lines.append(f"**Volume**: {ref['volume']}  ")
        if ref.get("pages"):
            lines.append(f"**Pages**: {ref['pages']}  ")

        return lines

    @staticmethod
    def _render_found_reference(ref: Dict) -> List[str]:
        """
        Render the found/matched reference section from academic database

        Args:
            ref: Reference dictionary

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append("\n##### Found Reference (From Academic Database)\n")

        if ref.get("matched_title"):
            lines.append(f"**Title**: {ref['matched_title']}  ")
        if ref.get("matched_authors"):
            lines.append(f"**Authors**: {ref['matched_authors']}  ")
        if ref.get("matched_year"):
            lines.append(f"**Year**: {ref['matched_year']}  ")
        if ref.get("matched_doi"):
            lines.append(
                f"**DOI**: [{ref['matched_doi']}](https://doi.org/{ref['matched_doi']})  "
            )
        if ref.get("matched_venue"):
            lines.append(f"**Venue**: {ref['matched_venue']}  ")
        if ref.get("matched_citation_count"):
            lines.append(f"**Citations**: {ref['matched_citation_count']}  ")
        if ref.get("matched_influential_citation_count"):
            lines.append(
                f"**Influential Citations**: {ref['matched_influential_citation_count']}  "
            )

        return lines

    @staticmethod
    def _render_verification_details(ref: Dict) -> List[str]:
        """
        Render verification details section

        Args:
            ref: Reference dictionary

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append("\n##### Verification Details\n")

        method = ReportGenerator._get_search_method(ref)
        if method:
            lines.append(f"**Search Method**: {method}  ")
        if ref.get("confidence"):
            lines.append(f"**Confidence Level**: {ref['confidence'].title()}  ")
        if ref.get("title_similarity"):
            lines.append(f"**Title Similarity**: {ref['title_similarity']:.1%}  ")
        if ref.get("author_overlap"):
            lines.append(f"**Author Overlap**: {ref['author_overlap']:.1%}  ")
        if ref.get("year_match") is not None:
            lines.append(f"**Year Match**: {'✓' if ref['year_match'] else '✗'}  ")

        return lines

    @staticmethod
    def _render_verified_reference(ref: Dict, index: int) -> List[str]:
        """
        Render a complete verified reference with collapsible details

        Args:
            ref: Reference dictionary
            index: Reference number

        Returns:
            List of markdown lines
        """
        lines = []
        title = ReportGenerator._get_reference_title(ref)
        lines.append(f"#### **{index}. {title}**")

        # Collapsible details section (collapsed by default)
        lines.append("<details>")
        lines.append("<summary>Show details</summary>\n")

        # Add all sections
        lines.extend(ReportGenerator._render_original_reference(ref))
        lines.extend(ReportGenerator._render_found_reference(ref))
        lines.extend(ReportGenerator._render_verification_details(ref))

        lines.append("</details>\n")
        return lines

    @staticmethod
    def _render_not_found_reference(ref: Dict, index: int) -> List[str]:
        """
        Render a not-found reference with collapsible details

        Args:
            ref: Reference dictionary
            index: Reference number

        Returns:
            List of markdown lines
        """
        lines = []
        title = ref.get("title") or "Unknown Title"
        lines.append(f"#### **{index}. {title}**")

        # Collapsible details section (collapsed by default)
        lines.append("<details>")
        lines.append("<summary>Show details</summary>\n")

        lines.extend(ReportGenerator._render_original_reference(ref))

        # Search details
        lines.append("\n### Search Details\n")
        method = ReportGenerator._get_search_method(ref)
        if method:
            lines.append(f"**Search Method**: {method}  ")
        lines.append("**Status**: Not found in academic databases  ")

        lines.append("</details>\n")
        return lines

    @staticmethod
    def _render_error_reference(ref: Dict, index: int) -> List[str]:
        """
        Render an error reference with collapsible details

        Args:
            ref: Reference dictionary
            index: Reference number

        Returns:
            List of markdown lines
        """
        lines = []
        title = ref.get("title") or ref.get("matched_title") or "Unknown Title"
        lines.append(f"#### **{index}. {title}**")

        # Collapsible details section (collapsed by default)
        lines.append("<details>")
        lines.append("<summary>Show details</summary>\n")

        # Error information
        if ref.get("error"):
            lines.append(f"##### Error\n**{ref['error']}**\n")

        lines.extend(ReportGenerator._render_original_reference(ref))

        # Found reference information (if any partial match)
        if any(
            ref.get(k)
            for k in ["matched_title", "matched_authors", "matched_year", "matched_doi"]
        ):
            lines.append("\n##### Partial Match Found\n")
            if ref.get("matched_title"):
                lines.append(f"**Title**: {ref['matched_title']}  ")
            if ref.get("matched_authors"):
                lines.append(f"**Authors**: {ref['matched_authors']}  ")
            if ref.get("matched_year"):
                lines.append(f"**Year**: {ref['matched_year']}  ")
            if ref.get("matched_doi"):
                lines.append(
                    f"**DOI**: [{ref['matched_doi']}](https://doi.org/{ref['matched_doi']})  "
                )

        lines.append("</details>\n")
        return lines

    @staticmethod
    def _render_unparsed_reference(ref: Dict, index: int) -> List[str]:
        """
        Render an unparsed reference with collapsible details

        Args:
            ref: Reference dictionary
            index: Reference number

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append(f"#### **{index}. Unable to Parse Reference**")

        # Collapsible details section (collapsed by default)
        lines.append("<details>")
        lines.append("<summary>Show details</summary>\n")

        lines.append("##### Parsing Failed\n")
        lines.append("Could not extract DOI or title from this reference.\n")

        if ref.get("raw_text"):
            lines.append(f"\n**Parsed reference**: `{ref['raw_text']}`")
        else:
            lines.append("\n*No text available*")

        lines.append("\n</details>\n")
        return lines

    def generate_summary(self) -> Dict:
        """
        Generate a summary report of the checking results

        Returns:
            Dictionary with summary statistics
        """
        total = len(self.results)
        valid_format = sum(1 for r in self.results if r.get("valid_format"))
        exists = sum(1 for r in self.results if r.get("exists"))
        invalid_format = total - valid_format if valid_format else 0
        not_found = valid_format - exists if valid_format else total - exists

        return {
            "total_references": total,
            "valid_format": valid_format,
            "invalid_format": invalid_format,
            "exists": exists,
            "not_found": not_found,
            "success_rate": (exists / total * 100) if total > 0 else 0,
        }

    def save_json(self, output_path: str):
        """
        Save detailed results to a JSON file

        Args:
            output_path: Path to save the JSON file
        """
        output_data = {
            "summary": self.generate_summary(),
            "references": self.results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Detailed results saved to: {output_path}")

    def generate_markdown(self) -> str:
        """
        Generate a human-readable markdown report grouping references by status and confidence

        Returns:
            Markdown-formatted report as string
        """
        summary = self.generate_summary()

        # Group references by category
        verified_high = []
        verified_medium = []
        verified_low = []
        not_found = []
        errors = []
        no_doi_or_title = []

        for ref in self.results:
            if ref.get("error"):
                if "No DOI or title" in ref.get("error", ""):
                    no_doi_or_title.append(ref)
                else:
                    errors.append(ref)
            elif ref.get("exists"):
                confidence = ref.get("confidence", "").lower()
                if confidence == "high":
                    verified_high.append(ref)
                elif confidence == "medium":
                    verified_medium.append(ref)
                elif confidence == "low":
                    verified_low.append(ref)
                else:
                    # DOI-based verification (no confidence level)
                    verified_high.append(ref)
            else:
                not_found.append(ref)

        # Build markdown report
        md = []
        md.append("# Reference Verification Report\n")

        # Summary section
        md.append("## Summary\n")
        md.append(f"- **Total References**: {summary['total_references']}")
        md.append(
            f"- **Successfully Verified**: {summary['exists']} ({summary['success_rate']:.1f}%)"
        )
        md.append(f"- **Not Found**: {len(not_found)}")
        md.append(f"- **Errors**: {len(errors)}")
        md.append(f"- **No DOI or Title**: {len(no_doi_or_title)}\n")

        # Table of Contents
        md.append("## Table of Contents\n")
        if verified_high:
            md.append(
                f"- [✅ Verified References - High Confidence ({len(verified_high)})](#-verified-references---high-confidence-{len(verified_high)})"
            )
        if verified_medium:
            md.append(
                f"- [✅ Verified References - Medium Confidence ({len(verified_medium)})](#-verified-references---medium-confidence-{len(verified_medium)})"
            )
        if verified_low:
            md.append(
                f"- [⚠️ Verified References - Low Confidence ({len(verified_low)})](#️-verified-references---low-confidence-{len(verified_low)})"
            )
        if not_found:
            md.append(
                f"- [❌ Not Found ({len(not_found)})](#-not-found-{len(not_found)})"
            )
        if errors:
            md.append(f"- [⚠️ Errors ({len(errors)})](#️-errors-{len(errors)})")
        if no_doi_or_title:
            md.append(
                f"- [⚠️ Missing DOI and Title ({len(no_doi_or_title)})](#️-missing-doi-and-title-{len(no_doi_or_title)})"
            )
        md.append("\n---\n")

        # Verified references - High confidence
        if verified_high:
            md.append(
                f"## ✅ Verified References - High Confidence ({len(verified_high)})\n"
            )
            md.append("<details>")
            md.append(
                "<summary>These references were successfully matched with high confidence (click to expand)</summary>\n"
            )
            for i, ref in enumerate(verified_high, 1):
                md.extend(self._render_verified_reference(ref, i))

            md.append("</details>\n")

        # Verified references - Medium confidence
        if verified_medium:
            md.append(
                f"## ✅ Verified References - Medium Confidence ({len(verified_medium)})\n"
            )
            md.append("<details open>")
            md.append(
                "<summary>These references were matched with medium confidence. Manual verification recommended.</summary>\n"
            )
            for i, ref in enumerate(verified_medium, 1):
                md.extend(self._render_verified_reference(ref, i))

            md.append("</details>\n")

        # Verified references - Low confidence
        if verified_low:
            md.append(
                f"## ⚠️ Verified References - Low Confidence ({len(verified_low)})\n"
            )
            md.append("<details open>")
            md.append(
                "<summary>These references had matches, but confidence is low. Manual verification strongly recommended.</summary>\n"
            )
            for i, ref in enumerate(verified_low, 1):
                md.extend(self._render_verified_reference(ref, i))

            md.append("</details>\n")

        # Not found references
        if not_found:
            md.append(f"## ❌ Not Found ({len(not_found)})\n")
            md.append("<details open>")
            md.append(
                "<summary>These references could not be found in academic databases.</summary>\n"
            )
            for i, ref in enumerate(not_found, 1):
                md.extend(self._render_not_found_reference(ref, i))

            md.append("</details>\n")

        # Errors
        if errors:
            md.append(f"## ⚠️ Errors ({len(errors)})\n")
            md.append("<details open>")
            md.append(
                "<summary>These references encountered errors during verification.</summary>\n"
            )
            for i, ref in enumerate(errors, 1):
                md.extend(self._render_error_reference(ref, i))

            md.append("</details>\n")

        # No DOI or Title
        if no_doi_or_title:
            md.append(f"## ⚠️ Missing DOI and Title ({len(no_doi_or_title)})\n")
            md.append("<details open>")
            md.append(
                "<summary>These references could not be parsed - no DOI or title was extracted.</summary>\n"
            )
            for i, ref in enumerate(no_doi_or_title, 1):
                md.extend(self._render_unparsed_reference(ref, i))

            md.append("</details>\n")

        return "\n".join(md)

    def save_markdown(self, output_path: str):
        """
        Save markdown report to a file

        Args:
            output_path: Path to save the markdown file
        """
        markdown = self.generate_markdown()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"✓ Markdown report saved to: {output_path}")
