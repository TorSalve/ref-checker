"""
Batch processing functionality for multiple DOIs
"""

import json
import csv
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from .core import DOI
from .enums import APISource
from .utils import clean_data_structure


class DOIBatch:
    """
    Class for batch processing multiple DOIs with rate limiting
    """

    def __init__(
        self,
        rate_limit: Optional[float] = 1.0,
        mailto: Optional[str] = None,
        semantic_scholar_api_key: Optional[str] = None,
    ):
        """
        Initialize a DOI batch processor

        Args:
            rate_limit: Delay in seconds between requests (default: 1.0 second)
                       Set to None to disable rate limiting
            mailto: Email address for polite API access (recommended)
            semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits
        """
        self.rate_limit = rate_limit
        self.mailto = mailto
        self.semantic_scholar_api_key = semantic_scholar_api_key
        self.results = []
        self.errors = []

    def _batch_fetch_semantic_scholar(
        self, dois: List[str], timeout: int = 10
    ) -> Dict[str, Optional[str]]:
        """
        Fetch abstracts for multiple DOIs using Semantic Scholar batch API

        Args:
            dois: List of DOI strings
            timeout: Request timeout in seconds

        Returns:
            Dictionary mapping DOI to abstract (or None if not found)
        """
        # Semantic Scholar batch API endpoint
        url = "https://api.semanticscholar.org/graph/v1/paper/batch"

        # Maximum 500 papers per request according to API docs
        batch_size = 500
        all_abstracts = {}

        for i in range(0, len(dois), batch_size):
            batch_dois = dois[i : i + batch_size]

            # Format DOIs with "DOI:" prefix for Semantic Scholar
            paper_ids = [f"DOI:{doi}" for doi in batch_dois]

            params = {"fields": "abstract,externalIds"}
            headers = {"Accept": "application/json"}

            # Add API key to headers if provided
            if self.semantic_scholar_api_key:
                headers["x-api-key"] = self.semantic_scholar_api_key

            try:
                response = requests.post(
                    url,
                    json={"ids": paper_ids},
                    params=params,
                    headers=headers,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    data = response.json()

                    # Map results back to original DOIs
                    for idx, paper in enumerate(data):
                        if paper and idx < len(batch_dois):
                            original_doi = batch_dois[idx]
                            abstract = paper.get("abstract")
                            all_abstracts[original_doi] = (
                                abstract.strip() if abstract else None
                            )
                        elif idx < len(batch_dois):
                            # Paper not found
                            all_abstracts[batch_dois[idx]] = None
                else:
                    # On error, mark all DOIs in this batch as None
                    for doi in batch_dois:
                        all_abstracts[doi] = None

            except Exception as e:
                # On exception, mark all DOIs in this batch as None
                for doi in batch_dois:
                    all_abstracts[doi] = None

        return all_abstracts

    def process_dois(
        self,
        dois: List[str],
        fields: Optional[List[str]] = None,
        timeout: int = 10,
        verbose: bool = True,
        source: Union[APISource, str] = APISource.AUTO,
        use_batch: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple DOIs and retrieve their metadata

        Args:
            dois: List of DOI strings
            fields: Optional list of fields to retrieve (e.g., ['title', 'abstract', 'authors'])
                   If None, retrieves common fields
            timeout: Request timeout in seconds per DOI
            verbose: Whether to print progress
            source: API source for abstract retrieval (APISource enum or string)
            use_batch: Whether to use batch API for Semantic Scholar (faster, recommended)

        Returns:
            List of dictionaries containing DOI metadata
        """
        self.results = []
        self.errors = []

        if fields is None:
            fields = ["title", "abstract", "authors", "year", "publisher", "doi"]

        total = len(dois)

        # Convert string source to enum
        if isinstance(source, str):
            try:
                source = APISource(source.lower())
            except ValueError:
                source = APISource.AUTO

        # Pre-fetch abstracts using batch API if using Semantic Scholar and abstract is needed
        semantic_scholar_abstracts = {}
        if (
            use_batch
            and "abstract" in fields
            and source in (APISource.SEMANTIC_SCHOLAR, APISource.AUTO)
        ):
            if verbose:
                print(
                    f"Batch fetching abstracts from Semantic Scholar for {total} DOIs..."
                )
            semantic_scholar_abstracts = self._batch_fetch_semantic_scholar(
                dois, timeout
            )
            if verbose:
                found = sum(1 for v in semantic_scholar_abstracts.values() if v)
                print(f"  Found {found}/{total} abstracts\n")

        for idx, doi_str in enumerate(dois, 1):
            if verbose:
                print(f"Processing {idx}/{total}: {doi_str}")

            try:
                doi_obj = DOI(
                    doi_str, semantic_scholar_api_key=self.semantic_scholar_api_key
                )
                result = self._extract_fields(
                    doi_obj,
                    fields,
                    timeout,
                    source,
                    semantic_scholar_abstracts.get(doi_str) if use_batch else None,
                )
                result["doi"] = doi_str
                result["status"] = "success"
                self.results.append(result)

                if verbose:
                    print(f"  ✓ Success")

            except Exception as e:
                error_result = {"doi": doi_str, "status": "error", "error": str(e)}
                self.results.append(error_result)
                self.errors.append(error_result)

                if verbose:
                    print(f"  ✗ Error: {e}")

            # Rate limiting (skip if we're using batch API since we already made the batch request)
            if (
                self.rate_limit
                and idx < total
                and not (use_batch and source == APISource.SEMANTIC_SCHOLAR)
            ):
                if verbose:
                    print(f"  Waiting {self.rate_limit}s...")
                time.sleep(self.rate_limit)

        if verbose:
            print(
                f"\nCompleted: {len(self.results) - len(self.errors)}/{total} successful"
            )

        return self.results

    def _extract_fields(
        self,
        doi_obj: DOI,
        fields: List[str],
        timeout: int,
        source: Union[APISource, str] = APISource.AUTO,
        prefetched_abstract: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract specified fields from a DOI object

        Args:
            doi_obj: DOI object
            fields: List of field names to extract
            timeout: Request timeout
            source: API source for abstract retrieval
            prefetched_abstract: Pre-fetched abstract from batch API (if available)

        Returns:
            Dictionary of extracted fields
        """
        result = {}
        metadata = None

        for field in fields:
            try:
                if field == "title":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    titles = metadata.get("title", [])
                    result["title"] = titles[0] if titles else None

                elif field == "abstract":
                    # Use pre-fetched abstract if available, otherwise fetch it
                    if prefetched_abstract is not None:
                        result["abstract"] = prefetched_abstract
                    else:
                        result["abstract"] = doi_obj.get_abstract(
                            source=source, timeout=timeout
                        )

                elif field == "authors":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    authors = metadata.get("author", [])
                    author_list = []
                    for author in authors:
                        given = author.get("given", "")
                        family = author.get("family", "")
                        full_name = f"{given} {family}".strip()
                        if full_name:
                            author_list.append(full_name)
                    result["authors"] = author_list

                elif field == "year":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    pub_date = metadata.get("published", {}).get("date-parts", [[]])[0]
                    result["year"] = (
                        pub_date[0] if pub_date and len(pub_date) > 0 else None
                    )

                elif field == "publisher":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    result["publisher"] = metadata.get("publisher", None)

                elif field == "doi":
                    result["doi"] = str(doi_obj)

                elif field == "url":
                    result["url"] = doi_obj.get_url()

                elif field == "type":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    result["type"] = metadata.get("type", None)

                elif field == "journal":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    containers = metadata.get("container-title", [])
                    result["journal"] = containers[0] if containers else None

                elif field == "citations":
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    result["citations"] = metadata.get("is-referenced-by-count", None)

                else:
                    # For any other field, try to get it from metadata
                    if metadata is None:
                        metadata = doi_obj.get_crossref_metadata(timeout=timeout)
                    result[field] = metadata.get(field, None)

            except Exception as e:
                result[field] = None

        return result

    def save_to_json(
        self,
        filepath: str,
        indent: int = 2,
        include_errors: bool = True,
        clean_data: bool = True,
    ) -> None:
        """
        Save results to a JSON file

        Args:
            filepath: Path to output JSON file
            indent: JSON indentation (default: 2)
            include_errors: Whether to include failed DOIs in output
            clean_data: Whether to clean text data (normalize whitespace)
        """
        output_data = (
            self.results
            if include_errors
            else [r for r in self.results if r.get("status") == "success"]
        )

        # Clean data if requested
        if clean_data:
            output_data = clean_data_structure(output_data, for_csv=False)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=indent, ensure_ascii=False)

        print(f"✓ Saved {len(output_data)} results to {filepath}")

    def save_to_csv(
        self,
        filepath: str,
        include_errors: bool = False,
        fields: Optional[List[str]] = None,
        clean_data: bool = True,
    ) -> None:
        """
        Save results to a CSV file

        Args:
            filepath: Path to output CSV file
            include_errors: Whether to include failed DOIs in output
            fields: Optional list of fields to include (if None, includes all)
            clean_data: Whether to clean text data (remove newlines, tabs, etc.)
        """
        output_data = (
            self.results
            if include_errors
            else [r for r in self.results if r.get("status") == "success"]
        )

        if not output_data:
            print("No data to save")
            return

        # Clean data for CSV if requested
        if clean_data:
            output_data = clean_data_structure(output_data, for_csv=True)

        # Determine fields
        if fields is None:
            # Get all unique fields from results
            all_fields = set()
            for result in output_data:
                all_fields.update(result.keys())
            fields = sorted(list(all_fields))

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()

            for result in output_data:
                # Convert lists to strings for CSV
                row = {}
                for field in fields:
                    value = result.get(field)
                    if isinstance(value, list):
                        row[field] = "; ".join(str(v) for v in value if v)
                    else:
                        row[field] = value
                writer.writerow(row)

        print(f"✓ Saved {len(output_data)} results to {filepath}")

    def get_errors(self) -> List[Dict[str, Any]]:
        """
        Get list of DOIs that failed to process

        Returns:
            List of error dictionaries
        """
        return self.errors

    def get_successful(self) -> List[Dict[str, Any]]:
        """
        Get list of successfully processed DOIs

        Returns:
            List of result dictionaries
        """
        return [r for r in self.results if r.get("status") == "success"]
