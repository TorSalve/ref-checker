"""
Reference validation and verification.

This module handles DOI validation and title-based paper search using
Semantic Scholar and CrossRef APIs.
"""

import re
import time
from typing import List, Dict, Optional
import requests
from tqdm import tqdm

from doi import DOI, validate_doi
from doi.exceptions import (
    DOIValidationError,
    DOIResolutionError,
    DOIMetadataError,
    DOIError,
)
from doi.query import SemanticScholarSearch
from doi.batch import DOIBatch


class ReferenceChecker:
    """Check validity of references using DOI lookup and title-based search"""

    def __init__(
        self, timeout: int = 10, semantic_scholar_api_key: Optional[str] = None
    ):
        """
        Initialize the reference checker

        Args:
            timeout: Timeout for DOI API requests in seconds
            semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits
        """
        self.timeout = timeout
        self.semantic_scholar_api_key = semantic_scholar_api_key
        self.semantic_scholar = SemanticScholarSearch(api_key=semantic_scholar_api_key)
        self.results: List[Dict] = []

    def _verify_author_match(self, ref_text: str, match_authors: List[Dict]) -> bool:
        """
        Verify at least one author surname matches between reference and search result

        Args:
            ref_text: Original reference text containing author names
            match_authors: List of author dicts from search result

        Returns:
            True if at least one author surname matches, or if verification not possible
        """
        if not match_authors:
            return True  # Can't verify, accept match

        # Extract surnames from reference text
        # Look for capitalized words at the start (before year or title)
        ref_surnames = set()

        # Common patterns: "Surname, Initial" or "Initial. Surname"
        author_patterns = [
            r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?),\s*[A-Z]",  # "Hassenzahl, M."
            r"\b[A-Z]\.\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)",  # "M. Hassenzahl"
            r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+and\b",  # "Hassenzahl and"
        ]

        for pattern in author_patterns:
            for match in re.finditer(pattern, ref_text):
                surname = match.group(1).lower()
                if len(surname) > 2:  # Skip initials
                    ref_surnames.add(surname)

        if not ref_surnames:
            return True  # Couldn't extract author names, accept match

        # Check if any surname appears in match authors
        for author in match_authors:
            author_name = author.get("name", "").lower()
            for surname in ref_surnames:
                if surname in author_name:
                    return True

        return False  # No author match found

    def check_doi(self, doi_string: str) -> Dict:
        """
        Check a single DOI for validity and retrieve metadata

        Args:
            doi_string: DOI string to check

        Returns:
            Dictionary with check results including title, authors, year
        """
        result = {
            "doi": doi_string,
            "valid_format": False,
            "exists": False,
            "title": None,
            "authors": None,
            "year": None,
            "error": None,
        }

        try:
            # Validate format
            result["valid_format"] = validate_doi(doi_string)

            if not result["valid_format"]:
                result["error"] = "Invalid DOI format"
                return result

            # Try to get metadata (this checks if DOI exists)
            doi_obj = DOI(doi_string)
            try:
                metadata = doi_obj.get_crossref_metadata(timeout=self.timeout)
                result["exists"] = True

                # Extract key information
                result["title"] = metadata.get("title", [None])[0]

                authors = metadata.get("author", [])
                if authors:
                    author_names = []
                    for author in authors[:3]:  # First 3 authors
                        if "family" in author:
                            name = (
                                author.get("given", "") + " " + author.get("family", "")
                            )
                            author_names.append(name.strip())
                    if len(authors) > 3:
                        author_names.append("et al.")
                    result["authors"] = ", ".join(author_names)

                # Get publication year
                published = metadata.get("published", {})
                if "date-parts" in published and published["date-parts"]:
                    result["year"] = published["date-parts"][0][0]
                elif "published-print" in metadata:
                    print_date = metadata["published-print"].get("date-parts", [[]])
                    if print_date and print_date[0]:
                        result["year"] = print_date[0][0]

            except (DOIMetadataError, DOIResolutionError) as e:
                result["error"] = f"DOI not found or inaccessible: {str(e)}"
                result["exists"] = False

        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def check_by_title(self, title: str, year: Optional[int] = None) -> Dict:
        """
        Check a reference by searching for its title using Semantic Scholar

        Args:
            title: Title of the paper to search for
            year: Optional publication year to improve matching

        Returns:
            Dictionary with check results including confidence level
        """
        result = {
            "doi": None,
            "title": title,
            "search_method": "title",
            "valid_format": None,
            "exists": False,
            "matched_title": None,
            "authors": None,
            "year": year,
            "confidence": None,
            "error": None,
        }

        if not title or len(title) < 10:
            result["error"] = "Title too short or missing"
            return result

        try:
            # Add delay to avoid rate limiting
            time.sleep(1.0)

            # Search Semantic Scholar for the title
            # Use the paper search API directly
            search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": title,
                "limit": 5,
                "fields": "title,authors,year,externalIds,citationCount",
            }

            headers = {"Accept": "application/json"}
            if self.semantic_scholar_api_key:
                headers["x-api-key"] = self.semantic_scholar_api_key

            response = requests.get(
                search_url, params=params, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            papers = data.get("data", [])

            if not papers:
                result["error"] = "No matching papers found"
                return result

            # Find best match (first result is usually most relevant)
            best_match = papers[0]

            # Calculate simple confidence based on title similarity
            matched_title = best_match.get("title", "")
            title_lower = title.lower()
            matched_lower = matched_title.lower()

            # Simple similarity check
            if title_lower == matched_lower:
                confidence = "high"
            elif title_lower in matched_lower or matched_lower in title_lower:
                confidence = "medium"
            else:
                # Check for substantial word overlap
                title_words = set(title_lower.split())
                matched_words = set(matched_lower.split())
                overlap = len(title_words & matched_words) / max(len(title_words), 1)
                if overlap > 0.7:
                    confidence = "medium"
                else:
                    confidence = "low"

            result["exists"] = True
            result["matched_title"] = matched_title
            result["confidence"] = confidence

            # Extract DOI if available
            external_ids = best_match.get("externalIds", {})
            if external_ids and "DOI" in external_ids:
                result["doi"] = external_ids["DOI"]

            # Extract authors
            authors = best_match.get("authors", [])
            if authors:
                author_names = []
                for author in authors[:3]:
                    author_names.append(author.get("name", ""))
                if len(authors) > 3:
                    author_names.append("et al.")
                result["authors"] = ", ".join(author_names)

            # Get year from match if not provided
            if not result["year"]:
                result["year"] = best_match.get("year")

        except requests.RequestException as e:
            result["error"] = f"Search failed: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def check_by_title_batch(
        self, references_with_titles: List[Dict[str, Optional[str]]]
    ) -> List[Dict]:
        """
        Check multiple references by title using Semantic Scholar bulk search API.
        Implements multi-result evaluation with intelligent scoring.

        Scoring system (160 points max):
        - Title similarity: 0-100 points
        - Author match: 30 points
        - Year proximity: 0-20 points
        - Citation count: 0-10 points

        Confidence thresholds:
        - High: score >= 120
        - Medium: score >= 90
        - Low: score >= 70
        - Reject: score < 70

        Args:
            references_with_titles: List of reference dictionaries with titles

        Returns:
            List of check results in the same order as input
        """
        results = []

        if not references_with_titles:
            return results

        # Use SemanticScholarSearch with bulk API
        searcher = SemanticScholarSearch(api_key=self.semantic_scholar_api_key)

        # Rate limiting configuration
        # Without API key: 100 requests per 5 minutes = ~0.33 req/sec → use 0.5 req/sec to be safe
        # With API key: 5000 requests per 5 minutes = ~16 req/sec → use 2 req/sec to be safe
        if self.semantic_scholar_api_key:
            delay_between_requests = 0.5  # 2 requests per second (very conservative)
        else:
            delay_between_requests = 2.0  # 0.5 requests per second (very safe)

        consecutive_429_errors = 0
        max_retries = 5

        # Create progress bar
        pbar = tqdm(
            total=len(references_with_titles),
            desc="Checking references",
            unit="ref",
            ncols=100,
        )

        for idx, ref in enumerate(references_with_titles, 1):
            title = ref.get("title", "")
            year = ref.get("year")

            result = {
                "doi": None,
                "title": title,
                "search_method": "title_batch",
                "valid_format": None,
                "exists": False,
                "matched_title": None,
                "authors": None,
                "year": year,
                "confidence": None,
                "error": None,
            }

            if not title or len(title) < 10:
                result["error"] = "Title too short or missing"
                results.append(result)
                pbar.update(1)
                continue

            # Retry logic with exponential backoff
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    # Add author surname to search query for better results
                    raw_text = ref.get("raw_text", "")
                    query = title

                    # Try to extract first author surname and add to query
                    if raw_text:
                        author_match = re.match(
                            r"^([A-Z][a-z]+(?:-[A-Z][a-z]+)?),\s*[A-Z]", raw_text
                        )
                        if author_match:
                            author_surname = author_match.group(1)
                            query = f"{author_surname} {title}"

                    # Use bulk search API for better efficiency
                    # Search with title and optionally year filter
                    search_params = {
                        "query": query,
                        "limit": 5,
                        "fields": [
                            "title",
                            "authors",
                            "year",
                            "externalIds",
                            "citationCount",
                        ],
                    }

                    # Add year filter if available (±2 years)
                    if year:
                        search_params["year"] = f"{year-2}-{year+2}"

                    search_results = searcher.bulk_search(
                        **search_params, timeout=self.timeout
                    )
                    papers = search_results.get("data", [])

                    # If no results with year filter, try again without year restriction
                    if not papers and year:
                        search_params_no_year = search_params.copy()
                        del search_params_no_year["year"]
                        search_results = searcher.bulk_search(
                            **search_params_no_year, timeout=self.timeout
                        )
                        papers = search_results.get("data", [])

                    if not papers:
                        result["error"] = (
                            f"No matching papers found (searched: '{query[:100]}...' in Semantic Scholar)"
                        )
                        results.append(result)
                        success = True
                        continue

                    # Multi-result evaluation: Score each paper and pick the best
                    best_match = None
                    best_score = -1

                    for paper in papers[:5]:  # Examine top 5 results
                        score = 0
                        paper_title = paper.get("title", "").lower()
                        paper_year = paper.get("year")
                        paper_authors = paper.get("authors", [])

                        # Calculate title similarity (0-100 points)
                        title_words = set(title.lower().split())
                        paper_words = set(paper_title.split())
                        title_overlap = len(title_words & paper_words) / max(
                            len(title_words), 1
                        )
                        score += title_overlap * 100

                        # Author match bonus (30 points)
                        if self._verify_author_match(
                            ref.get("raw_text", ""), paper_authors
                        ):
                            score += 30

                        # Year proximity bonus (20 points max, decays with distance)
                        if year and paper_year:
                            year_diff = abs(year - paper_year)
                            if year_diff == 0:
                                score += 20
                            elif year_diff == 1:
                                score += 15
                            elif year_diff == 2:
                                score += 10
                            elif year_diff <= 5:
                                score += 5

                        # Citation count tie-breaker (up to 10 points)
                        citation_count = paper.get("citationCount", 0)
                        if citation_count:
                            score += min(citation_count / 100, 10)

                        if score > best_score:
                            best_score = score
                            best_match = paper

                    # Calculate title overlap for diagnostics
                    matched_title = best_match.get("title", "")
                    title_lower = title.lower()
                    matched_lower = matched_title.lower()

                    title_words = set(title_lower.split())
                    matched_words = set(matched_lower.split())
                    overlap = len(title_words & matched_words) / max(
                        len(title_words), 1
                    )

                    # Verify author match
                    authors = best_match.get("authors", [])
                    author_match = self._verify_author_match(
                        ref.get("raw_text", ""), authors
                    )

                    # Reject if no author match and overlap is not very high
                    if not author_match and overlap < 0.9:
                        # Add diagnostic information
                        ref_text = ref.get("raw_text", "")
                        ref_authors = []

                        # Extract author surnames from reference text
                        for pattern in [
                            r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?),\s*[A-Z]",
                            r"\b[A-Z]\.\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)",
                            r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s+and\b",
                        ]:
                            for match in re.finditer(pattern, ref_text[:200]):
                                surname = match.group(1)
                                if len(surname) > 2 and surname not in ref_authors:
                                    ref_authors.append(surname)

                        ref_author_str = (
                            ", ".join(ref_authors[:5])
                            if ref_authors
                            else "Unable to extract"
                        )

                        # Get matched paper authors
                        author_names = [a.get("name", "") for a in authors[:5]]
                        author_list = (
                            ", ".join(author_names) if author_names else "None"
                        )

                        result["error"] = (
                            f"No author match (overlap: {overlap:.1%}). "
                            f"Reference authors: [{ref_author_str}], Found: [{author_list}]"
                        )
                        result["matched_title"] = matched_title
                        result["authors"] = author_list
                        result["confidence"] = None
                        if best_match.get("year"):
                            result["year"] = best_match.get("year")
                        results.append(result)
                        success = True
                        continue

                    # Determine confidence based on scoring system
                    if best_score >= 120:
                        confidence = "high"
                    elif best_score >= 90:
                        confidence = "medium"
                    elif best_score >= 70:
                        confidence = "low"
                    else:
                        # Reject matches below score threshold
                        result["error"] = (
                            f"Match quality too low (score: {best_score:.1f}/160, overlap: {overlap:.1%}). "
                            f"Expected: '{title[:80]}...', Found: '{matched_title[:80]}...'"
                        )
                        result["matched_title"] = matched_title
                        result["confidence"] = None

                        if authors:
                            author_names = [a.get("name", "") for a in authors[:5]]
                            result["authors"] = ", ".join(author_names)

                        if best_match.get("year"):
                            result["year"] = best_match.get("year")

                        external_ids = best_match.get("externalIds", {})
                        if external_ids and "DOI" in external_ids:
                            result["doi"] = external_ids["DOI"]

                        results.append(result)
                        success = True
                        continue

                    result["exists"] = True
                    result["matched_title"] = matched_title
                    result["confidence"] = confidence

                    # Extract DOI if available
                    external_ids = best_match.get("externalIds", {})
                    if external_ids and "DOI" in external_ids:
                        result["doi"] = external_ids["DOI"]

                    # Extract authors
                    if authors:
                        author_names = []
                        for author in authors[:3]:
                            author_names.append(author.get("name", ""))
                        if len(authors) > 3:
                            author_names.append("et al.")
                        result["authors"] = ", ".join(author_names)

                    # Get year from match if not provided
                    if not result["year"]:
                        result["year"] = best_match.get("year")

                    results.append(result)
                    success = True
                    consecutive_429_errors = 0

                except (requests.RequestException, DOIError) as e:
                    error_msg = str(e)
                    # If rate limited, implement exponential backoff
                    if "429" in error_msg:
                        retry_count += 1
                        consecutive_429_errors += 1

                        if retry_count < max_retries:
                            # Exponential backoff: 5s, 10s, 20s, 40s, 80s
                            backoff_delay = 5.0 * (2 ** (retry_count - 1))
                            time.sleep(backoff_delay)
                        else:
                            result["error"] = (
                                f"Rate limit exceeded after {max_retries} retries"
                            )
                            results.append(result)
                            success = True
                            if consecutive_429_errors > 3:
                                time.sleep(30.0)
                    else:
                        result["error"] = f"Search failed: {error_msg}"
                        results.append(result)
                        success = True

                except Exception as e:
                    result["error"] = f"Unexpected error: {str(e)}"
                    results.append(result)
                    success = True

            # Rate limiting delay between requests
            if success and idx < len(references_with_titles):
                time.sleep(delay_between_requests)

            pbar.update(1)

        pbar.close()
        return results

    def check_reference(self, reference: Dict[str, Optional[str]]) -> Dict:
        """
        Check a single reference (with DOI or title)

        Args:
            reference: Dictionary with reference information (doi, title, year, raw_text)

        Returns:
            Dictionary with check results
        """
        # Try DOI first if available
        if reference.get("doi"):
            result = self.check_doi(reference["doi"])
            result["raw_text"] = reference.get("raw_text", "")
            result["search_method"] = "doi"

            # If DOI lookup failed and we have a title, try title search as fallback
            if result.get("error") and reference.get("title"):
                result = self.check_by_title(reference["title"], reference.get("year"))
                result["raw_text"] = reference.get("raw_text", "")
                result["doi"] = reference.get(
                    "doi"
                )  # Keep the invalid DOI for reference
                result["search_method"] = "title (DOI fallback)"

            return result

        # Fall back to title search
        if reference.get("title"):
            result = self.check_by_title(reference["title"], reference.get("year"))
            result["raw_text"] = reference.get("raw_text", "")
            return result

        # No DOI or title found
        return {
            "doi": None,
            "title": None,
            "search_method": None,
            "valid_format": None,
            "exists": False,
            "authors": None,
            "year": None,
            "raw_text": reference.get("raw_text", ""),
            "error": "No DOI or title found in reference",
        }

    def check_references(
        self, references: List[Dict[str, Optional[str]]], verbose: bool = True
    ) -> List[Dict]:
        """
        Check multiple references using batch processing for efficiency

        Args:
            references: List of reference dictionaries to check
            verbose: Print progress information

        Returns:
            List of dictionaries with check results
        """
        self.results = []

        if verbose:
            print(f"\n{'='*70}")
            print(f"Checking {len(references)} references...")
            print(f"{'='*70}\n")

        # Separate references by type: DOI vs title-based
        doi_references = []
        title_references = []
        other_references = []

        for i, ref in enumerate(references):
            if ref.get("doi"):
                doi_references.append((i, ref))
            elif ref.get("title"):
                title_references.append((i, ref))
            else:
                other_references.append((i, ref))

        # Create a results array with None placeholders
        temp_results = [None] * len(references)

        # Process DOI references individually
        if doi_references:
            if verbose:
                print(f"Processing {len(doi_references)} references with DOIs...\n")

            for idx, (original_idx, reference) in enumerate(doi_references, 1):
                if verbose:
                    display_text = reference.get("doi", "")
                    print(f"[{idx}/{len(doi_references)}] Checking DOI: {display_text}")

                result = self.check_doi(reference["doi"])
                result["raw_text"] = reference.get("raw_text", "")
                result["search_method"] = "doi"

                # If DOI lookup failed and we have a title, try title search as fallback
                if result.get("error") and reference.get("title"):
                    result = self.check_by_title(
                        reference["title"], reference.get("year")
                    )
                    result["raw_text"] = reference.get("raw_text", "")
                    result["doi"] = reference.get(
                        "doi"
                    )  # Keep the invalid DOI for reference
                    result["search_method"] = "title (DOI fallback)"

                temp_results[original_idx] = result

                if verbose:
                    if result["exists"]:
                        search_method_display = (
                            " (DOI)"
                            if result["search_method"] == "doi"
                            else " (title fallback)"
                        )
                        print(
                            f"  ✓ VALID{search_method_display} - {result.get('title')}"
                        )
                        if result["authors"]:
                            print(f"    Authors: {result['authors']}")
                        if result["year"]:
                            print(f"    Year: {result['year']}")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        if result.get("valid_format"):
                            print(f"  ✗ NOT FOUND (DOI) - {error_msg}")
                        else:
                            print(f"  ✗ INVALID DOI FORMAT - {error_msg}")
                    print()

        # Process title-based references in batch
        if title_references:
            if verbose:
                print(
                    f"\nProcessing {len(title_references)} references by title (batch mode)...\n"
                )

            # Extract just the references for batch processing
            refs_for_batch = [ref for _, ref in title_references]
            batch_results = self.check_by_title_batch(refs_for_batch)

            # Map results back to original positions
            for (original_idx, reference), result in zip(
                title_references, batch_results
            ):
                result["raw_text"] = reference.get("raw_text", "")
                temp_results[original_idx] = result

                if verbose:
                    # Find position in title_references list
                    title_idx = [
                        i
                        for i, (oi, _) in enumerate(title_references)
                        if oi == original_idx
                    ][0]
                    display_text = reference.get("title", "")[:50]
                    print(
                        f"[{title_idx + 1}/{len(title_references)}] {display_text}..."
                    )

                    if result["exists"]:
                        confidence = result.get("confidence", "unknown")
                        print(
                            f"  ✓ FOUND (title, {confidence} confidence) - {result.get('matched_title')}"
                        )
                        if result.get("doi"):
                            print(f"    DOI: {result['doi']}")
                        if result["authors"]:
                            print(f"    Authors: {result['authors']}")
                        if result["year"]:
                            print(f"    Year: {result['year']}")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        print(f"  ✗ NOT FOUND (title search) - {error_msg}")
                    print()

        # Process other references (no DOI or title)
        if other_references:
            if verbose:
                print(
                    f"\nProcessing {len(other_references)} references without DOI or title...\n"
                )

            for idx, (original_idx, reference) in enumerate(other_references, 1):
                result = {
                    "doi": None,
                    "title": None,
                    "search_method": None,
                    "valid_format": None,
                    "exists": False,
                    "authors": None,
                    "year": None,
                    "raw_text": reference.get("raw_text", ""),
                    "error": "No DOI or title found in reference",
                }
                temp_results[original_idx] = result

                if verbose:
                    print(f"[{idx}/{len(other_references)}] No extractable information")
                    print(f"  ✗ ERROR - {result['error']}\n")

        # Compile final results in original order
        self.results = [r for r in temp_results if r is not None]

        return self.results

    def generate_report(self) -> Dict:
        """
        Generate a summary report of the checking results

        Returns:
            Dictionary with summary statistics
        """
        total = len(self.results)
        # Count references by category (matching reporter.py logic)
        exists = sum(1 for r in self.results if r.get("exists"))
        has_error = sum(1 for r in self.results if r.get("error"))
        not_found = sum(
            1 for r in self.results if not r.get("exists") and not r.get("error")
        )

        # Legacy metrics (kept for backwards compatibility)
        valid_format = sum(1 for r in self.results if r.get("valid_format"))
        invalid_format = total - valid_format

        report = {
            "total_references": total,
            "valid_format": valid_format,
            "invalid_format": invalid_format,
            "exists": exists,
            "not_found": not_found,
            "errors": has_error,
            "success_rate": (exists / total * 100) if total > 0 else 0,
        }

        return report

    def print_report(self):
        """Print a formatted summary report"""
        report = self.generate_report()

        print(f"\n{'='*70}")
        print("REFERENCE CHECK SUMMARY")
        print(f"{'='*70}")
        print(f"Total references found:        {report['total_references']}")
        print(f"Valid DOI format:              {report['valid_format']}")
        print(f"Invalid DOI format:            {report['invalid_format']}")
        print(f"References verified (exist):   {report['exists']}")
        print(f"References not found:          {report['not_found']}")
        print(f"References with errors:        {report['errors']}")
        print(f"Success rate:                  {report['success_rate']:.1f}%")
        print(f"{'='*70}\n")
