"""
Convenience API functions for common DOI operations
"""

from typing import Optional, Dict, Any, List, Union

from .core import DOI
from .query import DOIQuery, SemanticScholarSearch
from .batch import DOIBatch
from .enums import APISource


# Single DOI convenience functions


def resolve_doi(doi: str, timeout: int = 10) -> str:
    """
    Convenience function to resolve a DOI

    Args:
        doi: DOI string
        timeout: Request timeout in seconds

    Returns:
        Resolved target URL
    """
    doi_obj = DOI(doi)
    return doi_obj.resolve(timeout=timeout)


def get_doi_metadata(doi: str, format: str = "json", timeout: int = 10) -> Any:
    """
    Convenience function to get metadata for a DOI

    Args:
        doi: DOI string
        format: Desired format (json, bibtex, etc.)
        timeout: Request timeout in seconds

    Returns:
        Metadata in the requested format
    """
    doi_obj = DOI(doi)
    return doi_obj.get_metadata(format=format, timeout=timeout)


def get_doi_citation(doi: str, style: str = "apa", timeout: int = 10) -> str:
    """
    Convenience function to get a formatted citation for a DOI

    Args:
        doi: DOI string
        style: Citation style (apa, mla, chicago, etc.)
        timeout: Request timeout in seconds

    Returns:
        Formatted citation string
    """
    doi_obj = DOI(doi)
    return doi_obj.get_citation(style=style, timeout=timeout)


def validate_doi(doi: str) -> bool:
    """
    Convenience function to validate a DOI format

    Args:
        doi: DOI string to validate

    Returns:
        True if valid, False otherwise
    """
    doi_obj = DOI(doi, validate=False)
    return doi_obj.is_valid()


def search_dois(
    query: str,
    rows: int = 20,
    mailto: Optional[str] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    Convenience function to search for DOIs

    Args:
        query: Search query string
        rows: Number of results to return
        mailto: Email address for polite API access
        timeout: Request timeout in seconds

    Returns:
        Dictionary with search results
    """
    query_obj = DOIQuery(mailto=mailto)
    return query_obj.search(query=query, rows=rows, timeout=timeout)


def get_doi_abstract(
    doi: str,
    source: Union[APISource, str] = APISource.AUTO,
    timeout: int = 10,
    semantic_scholar_api_key: Optional[str] = None,
) -> Optional[str]:
    """
    Convenience function to get the abstract for a DOI

    Args:
        doi: DOI string
        source: API source to use (APISource enum or string)
        timeout: Request timeout in seconds
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        Abstract text if available, None otherwise
    """
    doi_obj = DOI(doi, semantic_scholar_api_key=semantic_scholar_api_key)
    return doi_obj.get_abstract(source=source, timeout=timeout)


# Batch processing convenience functions


def process_dois_to_json(
    dois: List[str],
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = None,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process DOIs and save to JSON

    Args:
        dois: List of DOI strings
        output_file: Path to output JSON file
        fields: Optional list of fields to retrieve
        rate_limit: Optional delay in seconds between requests
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results
    """
    batch = DOIBatch(
        rate_limit=rate_limit, semantic_scholar_api_key=semantic_scholar_api_key
    )
    results = batch.process_dois(
        dois,
        fields=fields,
        timeout=timeout,
        verbose=verbose,
        source=source,
        use_batch=use_batch,
    )
    batch.save_to_json(output_file, clean_data=clean_data)
    return results


def process_dois_to_csv(
    dois: List[str],
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = None,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process DOIs and save to CSV

    Args:
        dois: List of DOI strings
        output_file: Path to output CSV file
        fields: Optional list of fields to retrieve
        rate_limit: Optional delay in seconds between requests
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data (remove newlines, tabs)
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results
    """
    batch = DOIBatch(
        rate_limit=rate_limit, semantic_scholar_api_key=semantic_scholar_api_key
    )
    results = batch.process_dois(
        dois,
        fields=fields,
        timeout=timeout,
        verbose=verbose,
        source=source,
        use_batch=use_batch,
    )
    batch.save_to_csv(output_file, fields=fields, clean_data=clean_data)
    return results


# Comma-separated DOI string convenience functions


def process_doi_string(
    doi_string: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = None,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process a comma-separated string of DOIs

    Args:
        doi_string: Comma-separated string of DOIs (e.g., "10.1145/xxx, 10.1038/yyy, 10.1109/zzz")
        fields: Optional list of fields to retrieve (e.g., ['title', 'abstract', 'authors'])
        rate_limit: Optional delay in seconds between requests
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of result dictionaries

    Examples:
        >>> from doi import process_doi_string
        >>>
        >>> # Process comma-separated DOIs
        >>> results = process_doi_string(
        ...     "10.1145/3290605.3300233, 10.1038/nature12373",
        ...     fields=["title", "abstract"]
        ... )
        >>>
        >>> # With API key
        >>> results = process_doi_string(
        ...     dois_string,
        ...     semantic_scholar_api_key="your-key"
        ... )
    """
    # Parse comma-separated DOI string
    dois = [doi.strip() for doi in doi_string.split(",") if doi.strip()]

    if not dois:
        raise ValueError("No valid DOIs found in input string")

    # Process DOIs
    batch = DOIBatch(
        rate_limit=rate_limit, semantic_scholar_api_key=semantic_scholar_api_key
    )
    results = batch.process_dois(
        dois,
        fields=fields,
        timeout=timeout,
        verbose=verbose,
        source=source,
        use_batch=use_batch,
    )
    return results


def process_doi_string_to_json(
    doi_string: str,
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = None,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process comma-separated DOIs and save to JSON

    Args:
        doi_string: Comma-separated string of DOIs (e.g., "10.1145/xxx, 10.1038/yyy")
        output_file: Path to output JSON file
        fields: Optional list of fields to retrieve
        rate_limit: Optional delay in seconds between requests
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results

    Examples:
        >>> from doi import process_doi_string_to_json
        >>>
        >>> # Process and save to JSON
        >>> results = process_doi_string_to_json(
        ...     "10.1145/3290605.3300233, 10.1038/nature12373",
        ...     "results.json",
        ...     fields=["title", "abstract", "authors"]
        ... )
    """
    # Parse comma-separated DOI string
    dois = [doi.strip() for doi in doi_string.split(",") if doi.strip()]

    if not dois:
        raise ValueError("No valid DOIs found in input string")

    # Process and save
    return process_dois_to_json(
        dois=dois,
        output_file=output_file,
        fields=fields,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
        source=source,
        clean_data=clean_data,
        use_batch=use_batch,
        semantic_scholar_api_key=semantic_scholar_api_key,
    )


def process_doi_string_to_csv(
    doi_string: str,
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = None,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process comma-separated DOIs and save to CSV

    Args:
        doi_string: Comma-separated string of DOIs (e.g., "10.1145/xxx, 10.1038/yyy")
        output_file: Path to output CSV file
        fields: Optional list of fields to retrieve
        rate_limit: Optional delay in seconds between requests
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data (remove newlines, tabs)
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results

    Examples:
        >>> from doi import process_doi_string_to_csv
        >>>
        >>> # Process and save to CSV
        >>> results = process_doi_string_to_csv(
        ...     "10.1145/3290605.3300233, 10.1038/nature12373, 10.1109/CVPR.2016.90",
        ...     "results.csv",
        ...     fields=["title", "abstract", "authors", "year"]
        ... )
    """
    # Parse comma-separated DOI string
    dois = [doi.strip() for doi in doi_string.split(",") if doi.strip()]

    if not dois:
        raise ValueError("No valid DOIs found in input string")

    # Process and save
    return process_dois_to_csv(
        dois=dois,
        output_file=output_file,
        fields=fields,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
        source=source,
        clean_data=clean_data,
        use_batch=use_batch,
        semantic_scholar_api_key=semantic_scholar_api_key,
    )


# File-based convenience functions


def process_doi_file(
    input_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = 1.0,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process DOIs from a file containing comma-separated DOI strings

    Args:
        input_file: Path to file containing comma-separated DOIs (one line or multiple lines)
        fields: Optional list of fields to retrieve (e.g., ['title', 'abstract', 'authors'])
        rate_limit: Delay in seconds between requests (default: 1.0 second)
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of result dictionaries

    Examples:
        >>> from doi import process_doi_file
        >>>
        >>> # Process DOIs from a file
        >>> results = process_doi_file(
        ...     "dois.txt",
        ...     fields=["title", "abstract", "authors"]
        ... )
        >>>
        >>> # File content can be:
        >>> # 10.1145/xxx, 10.1038/yyy, 10.1109/zzz
        >>> # Or multiple lines:
        >>> # 10.1145/xxx
        >>> # 10.1038/yyy
        >>> # 10.1109/zzz
    """
    # Read DOI string from file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"File {input_file} is empty or contains no valid DOIs")

    # Replace newlines with commas to handle multi-line files
    content = content.replace("\n", ",").replace("\r", ",")

    # Process using the string processor
    return process_doi_string(
        doi_string=content,
        fields=fields,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
        source=source,
        use_batch=use_batch,
        semantic_scholar_api_key=semantic_scholar_api_key,
    )


def process_doi_file_to_json(
    input_file: str,
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = 1.0,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process DOIs from a file and save to JSON

    Args:
        input_file: Path to file containing comma-separated DOIs
        output_file: Path to output JSON file
        fields: Optional list of fields to retrieve
        rate_limit: Delay in seconds between requests (default: 1.0 second)
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results

    Examples:
        >>> from doi import process_doi_file_to_json
        >>>
        >>> # Read DOIs from file, save to JSON
        >>> results = process_doi_file_to_json(
        ...     "dois.txt",
        ...     "results.json",
        ...     fields=["title", "abstract", "authors", "year"]
        ... )
    """
    # Read DOI string from file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"File {input_file} is empty or contains no valid DOIs")

    # Replace newlines with commas to handle multi-line files
    content = content.replace("\n", ",").replace("\r", ",")

    # Process and save
    return process_doi_string_to_json(
        doi_string=content,
        output_file=output_file,
        fields=fields,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
        source=source,
        clean_data=clean_data,
        use_batch=use_batch,
        semantic_scholar_api_key=semantic_scholar_api_key,
    )


def process_doi_file_to_csv(
    input_file: str,
    output_file: str,
    fields: Optional[List[str]] = None,
    rate_limit: Optional[float] = 1.0,
    timeout: int = 10,
    verbose: bool = True,
    source: Union[APISource, str] = APISource.AUTO,
    clean_data: bool = True,
    use_batch: bool = True,
    semantic_scholar_api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to process DOIs from a file and save to CSV

    Args:
        input_file: Path to file containing comma-separated DOIs
        output_file: Path to output CSV file
        fields: Optional list of fields to retrieve
        rate_limit: Delay in seconds between requests (default: 1.0 second)
        timeout: Request timeout in seconds
        verbose: Whether to print progress
        source: API source for abstract retrieval
        clean_data: Whether to clean text data (remove newlines, tabs)
        use_batch: Whether to use Semantic Scholar batch API (faster, recommended)
        semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

    Returns:
        List of results

    Examples:
        >>> from doi import process_doi_file_to_csv
        >>>
        >>> # Read DOIs from file, save to CSV
        >>> results = process_doi_file_to_csv(
        ...     "dois.txt",
        ...     "results.csv",
        ...     fields=["doi", "title", "abstract", "authors", "year"]
        ... )
    """
    # Read DOI string from file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"File {input_file} is empty or contains no valid DOIs")

    # Replace newlines with commas to handle multi-line files
    content = content.replace("\n", ",").replace("\r", ",")

    # Process and save
    return process_doi_string_to_csv(
        doi_string=content,
        output_file=output_file,
        fields=fields,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
        source=source,
        clean_data=clean_data,
        use_batch=use_batch,
        semantic_scholar_api_key=semantic_scholar_api_key,
    )


# Semantic Scholar bulk search convenience functions


def semantic_scholar_bulk_search(
    query: Optional[str] = None,
    year: Optional[str] = None,
    publication_types: Optional[List[str]] = None,
    open_access_pdf: Optional[bool] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    limit: int = 100,
    token: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Convenience function for Semantic Scholar bulk search (single page)

    Args:
        query: Search query string (searches in title, abstract, authors)
        year: Publication year filter (e.g., "2020", "2019-2021", "2015-")
        publication_types: List of publication types (e.g., ["JournalArticle", "Conference"])
        open_access_pdf: Filter for papers with open access PDFs
        venue: List of venue names to filter by
        fields_of_study: List of fields (e.g., ["Computer Science", "Medicine"])
        fields: Paper fields to return (e.g., ["title", "abstract", "authors", "year"])
        limit: Maximum number of results per page (max 1000)
        token: Pagination token from previous response
        api_key: Optional Semantic Scholar API key
        timeout: Request timeout in seconds

    Returns:
        Dictionary with search results

    Example:
        >>> from doi import semantic_scholar_bulk_search
        >>>
        >>> results = semantic_scholar_bulk_search(
        ...     query="deep learning",
        ...     year="2023",
        ...     fields_of_study=["Computer Science"],
        ...     limit=100
        ... )
        >>> print(f"Found {results['total']} papers")
        >>> for paper in results['data']:
        ...     print(paper['title'])
    """
    searcher = SemanticScholarSearch(api_key=api_key)
    return searcher.bulk_search(
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


def semantic_scholar_search_all(
    query: Optional[str] = None,
    year: Optional[str] = None,
    publication_types: Optional[List[str]] = None,
    open_access_pdf: Optional[bool] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    max_results: Optional[int] = None,
    rate_limit: float = 1.0,
    api_key: Optional[str] = None,
    timeout: int = 30,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve all papers matching search criteria (auto-pagination)

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
        api_key: Optional Semantic Scholar API key
        timeout: Request timeout in seconds
        verbose: Print progress information

    Returns:
        List of all matching papers

    Example:
        >>> from doi import semantic_scholar_search_all
        >>>
        >>> papers = semantic_scholar_search_all(
        ...     query="neural networks",
        ...     year="2023",
        ...     fields_of_study=["Computer Science"],
        ...     max_results=500,
        ...     verbose=True
        ... )
        >>> print(f"Retrieved {len(papers)} papers")
    """
    searcher = SemanticScholarSearch(api_key=api_key)
    return searcher.search_all(
        query=query,
        year=year,
        publication_types=publication_types,
        open_access_pdf=open_access_pdf,
        venue=venue,
        fields_of_study=fields_of_study,
        fields=fields,
        max_results=max_results,
        rate_limit=rate_limit,
        timeout=timeout,
        verbose=verbose,
    )
