"""
DOI query and search functionality
"""

import requests
import time
from typing import Optional, Dict, Any, List

from .exceptions import DOIError


class DOIQuery:
    """
    Class for querying DOI databases (primarily CrossRef)
    """

    CROSSREF_WORKS_API = "https://api.crossref.org/works"

    def __init__(self, mailto: Optional[str] = None):
        """
        Initialize a DOI query object

        Args:
            mailto: Email address for polite API access (recommended)
        """
        self.mailto = mailto

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Accept": "application/json"}
        if self.mailto:
            headers["User-Agent"] = f"DOILibrary/1.0 (mailto:{self.mailto})"
        return headers

    def search(
        self,
        query: str,
        rows: int = 20,
        offset: int = 0,
        sort: Optional[str] = None,
        order: str = "desc",
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for DOIs using CrossRef API

        Args:
            query: Search query string
            rows: Number of results to return (max 1000)
            offset: Starting offset for pagination
            sort: Field to sort by (score, updated, deposited, indexed, published, etc.)
            order: Sort order (asc or desc)
            timeout: Request timeout in seconds

        Returns:
            Dictionary with search results

        Raises:
            DOIError: If search fails
        """
        params = {
            "query": query,
            "rows": rows,
            "offset": offset,
        }

        if sort:
            params["sort"] = sort
            params["order"] = order

        try:
            response = requests.get(
                self.CROSSREF_WORKS_API,
                params=params,
                headers=self._get_headers(),
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise DOIError(f"Search failed: {str(e)}")

    def filter(
        self,
        filters: Dict[str, Any],
        rows: int = 20,
        offset: int = 0,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """
        Filter DOIs using CrossRef API filters

        Args:
            filters: Dictionary of filter criteria (e.g., {"type": "journal-article"})
            rows: Number of results to return
            offset: Starting offset for pagination
            timeout: Request timeout in seconds

        Returns:
            Dictionary with filtered results

        Raises:
            DOIError: If filtering fails
        """
        # Build filter string
        filter_parts = [f"{k}:{v}" for k, v in filters.items()]
        filter_string = ",".join(filter_parts)

        params = {
            "filter": filter_string,
            "rows": rows,
            "offset": offset,
        }

        try:
            response = requests.get(
                self.CROSSREF_WORKS_API,
                params=params,
                headers=self._get_headers(),
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise DOIError(f"Filter query failed: {str(e)}")


class SemanticScholarSearch:
    """
    Class for searching papers using Semantic Scholar bulk search API

    The bulk search endpoint allows for efficient retrieval of large numbers of papers
    matching specific criteria like publication year, fields of study, venue, etc.
    """

    BULK_SEARCH_API = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize a Semantic Scholar search object

        Args:
            api_key: Optional Semantic Scholar API key for higher rate limits
        """
        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def bulk_search(
        self,
        query: Optional[str] = None,
        year: Optional[str] = None,
        publication_types: Optional[List[str]] = None,
        open_access_pdf: Optional[bool] = None,
        venue: Optional[List[str]] = None,
        fields_of_study: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100,
        token: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Perform a bulk search for papers using Semantic Scholar API

        Args:
            query: Search query string (searches in title, abstract, authors)
            year: Publication year filter (e.g., "2020", "2019-2021", "2015-")
            publication_types: List of publication types (e.g., ["JournalArticle", "Conference"])
            open_access_pdf: Filter for papers with open access PDFs
            venue: List of venue names to filter by
            fields_of_study: List of fields (e.g., ["Computer Science", "Medicine"])
            fields: Paper fields to return (e.g., ["title", "abstract", "authors", "year"])
                   Default includes: paperId, externalIds, title, abstract, venue, year,
                   authors, citationCount, influentialCitationCount, isOpenAccess, fieldsOfStudy
            limit: Maximum number of results per page (max 1000)
            token: Pagination token from previous response
            timeout: Request timeout in seconds

        Returns:
            Dictionary with:
                - total: Total number of matching papers
                - data: List of paper objects
                - token: Pagination token for next page (if available)

        Raises:
            DOIError: If search fails

        Example:
            >>> searcher = SemanticScholarSearch(api_key="your-key")
            >>> results = searcher.bulk_search(
            ...     query="machine learning",
            ...     year="2020-2023",
            ...     fields_of_study=["Computer Science"],
            ...     limit=100
            ... )
            >>> print(f"Found {results['total']} papers")
            >>> for paper in results['data']:
            ...     print(paper['title'])
        """
        params = {}

        # Add query parameters if provided
        if query:
            params["query"] = query
        if year:
            params["year"] = year
        if publication_types:
            params["publicationTypes"] = ",".join(publication_types)
        if open_access_pdf is not None:
            params["openAccessPdf"] = str(open_access_pdf).lower()
        if venue:
            params["venue"] = ",".join(venue)
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        if fields:
            params["fields"] = ",".join(fields)
        if limit:
            params["limit"] = min(limit, 1000)  # API max is 1000
        if token:
            params["token"] = token

        try:
            response = requests.get(
                self.BULK_SEARCH_API,
                params=params,
                headers=self._get_headers(),
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise DOIError(f"Semantic Scholar bulk search failed: {str(e)}")

    def search_all(
        self,
        query: Optional[str] = None,
        year: Optional[str] = None,
        publication_types: Optional[List[str]] = None,
        open_access_pdf: Optional[bool] = None,
        venue: Optional[List[str]] = None,
        fields_of_study: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        max_results: Optional[int] = None,
        rate_limit: float = 1.0,
        timeout: int = 30,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all papers matching search criteria (handles pagination automatically)

        Args:
            query: Search query string
            year: Publication year filter
            publication_types: List of publication types
            open_access_pdf: Filter for open access PDFs
            venue: List of venue names
            fields_of_study: List of fields of study
            fields: Paper fields to return
            max_results: Maximum total results to retrieve (None = all)
            rate_limit: Seconds to wait between requests (default 1.0)
            timeout: Request timeout in seconds
            verbose: Print progress information

        Returns:
            List of all matching papers

        Raises:
            DOIError: If search fails

        Example:
            >>> searcher = SemanticScholarSearch(api_key="your-key")
            >>> papers = searcher.search_all(
            ...     query="neural networks",
            ...     year="2023",
            ...     fields_of_study=["Computer Science"],
            ...     max_results=500,
            ...     verbose=True
            ... )
            >>> print(f"Retrieved {len(papers)} papers")
        """
        all_papers = []
        token = None
        page = 0

        while True:
            page += 1

            # Calculate limit for this request
            if max_results:
                remaining = max_results - len(all_papers)
                if remaining <= 0:
                    break
                limit = min(1000, remaining)
            else:
                limit = 1000

            if verbose:
                print(f"Fetching page {page} (limit={limit})...")

            # Make request
            results = self.bulk_search(
                query=query,
                year=year,
                publication_types=publication_types,
                open_access_pdf=open_access_pdf,
                venue=venue,
                fields_of_study=fields_of_study,
                fields=fields,
                limit=limit,
                token=token,
                timeout=timeout,
            )

            # Extract papers
            papers = results.get("data", [])
            if not papers:
                break

            all_papers.extend(papers)

            if verbose:
                total = results.get("total", "unknown")
                print(
                    f"  Retrieved {len(papers)} papers (total so far: {len(all_papers)}/{total})"
                )

            # Check for next page
            token = results.get("token")
            if not token:
                break

            # Check if we've reached max_results
            if max_results and len(all_papers) >= max_results:
                break

            # Rate limiting
            if rate_limit and rate_limit > 0:
                time.sleep(rate_limit)

        if verbose:
            print(f"Complete! Retrieved {len(all_papers)} total papers")

        return all_papers
