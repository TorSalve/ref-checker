"""
Core DOI class for single DOI operations
"""

import re
import requests
from typing import Optional, Dict, Any, Union

from .exceptions import DOIValidationError, DOIResolutionError, DOIMetadataError
from .enums import APISource


class DOI:
    """
    Main class for interacting with DOI REST APIs

    Attributes:
        BASE_URL: Base URL for doi.org resolution
        CROSSREF_API: CrossRef REST API endpoint
        DATACITE_API: DataCite REST API endpoint
    """

    BASE_URL = "https://doi.org"
    CROSSREF_API = "https://api.crossref.org/works"
    DATACITE_API = "https://api.datacite.org/dois"

    # DOI regex pattern (simplified version)
    DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")

    def __init__(
        self,
        doi: str,
        validate: bool = True,
        semantic_scholar_api_key: Optional[str] = None,
    ):
        """
        Initialize a DOI object

        Args:
            doi: The DOI string (with or without "doi:" or "https://doi.org/" prefix)
            validate: Whether to validate the DOI format
            semantic_scholar_api_key: Optional Semantic Scholar API key for higher rate limits

        Raises:
            DOIValidationError: If the DOI format is invalid and validate=True
        """
        self.raw_doi = doi
        self.doi = self._clean_doi(doi)
        self.semantic_scholar_api_key = semantic_scholar_api_key

        if validate and not self.is_valid():
            raise DOIValidationError(f"Invalid DOI format: {doi}")

    def _clean_doi(self, doi: str) -> str:
        """
        Clean and normalize a DOI string

        Args:
            doi: Raw DOI string

        Returns:
            Cleaned DOI string (e.g., "10.1234/example")
        """
        # Remove common prefixes
        doi = doi.strip()
        doi = re.sub(r"^doi:", "", doi, flags=re.IGNORECASE)
        doi = re.sub(r"^https?://doi\.org/", "", doi, flags=re.IGNORECASE)
        doi = re.sub(r"^https?://dx\.doi\.org/", "", doi, flags=re.IGNORECASE)

        return doi

    def is_valid(self) -> bool:
        """
        Check if the DOI format is valid

        Returns:
            True if valid, False otherwise
        """
        return bool(self.DOI_PATTERN.match(self.doi))

    def get_url(self) -> str:
        """
        Get the full DOI URL

        Returns:
            Full DOI URL (e.g., "https://doi.org/10.1234/example")
        """
        return f"{self.BASE_URL}/{self.doi}"

    def resolve(self, timeout: int = 10) -> str:
        """
        Resolve the DOI to its target URL

        Args:
            timeout: Request timeout in seconds

        Returns:
            The resolved target URL

        Raises:
            DOIResolutionError: If the DOI cannot be resolved
        """
        try:
            response = requests.head(
                self.get_url(), allow_redirects=True, timeout=timeout
            )
            response.raise_for_status()
            return response.url
        except requests.RequestException as e:
            raise DOIResolutionError(f"Failed to resolve DOI {self.doi}: {str(e)}")

    def get_metadata(self, format: str = "json", timeout: int = 10) -> Any:
        """
        Retrieve metadata for the DOI in various formats

        Args:
            format: Desired format (json, bibtex, crossref-xml, datacite-xml, etc.)
            timeout: Request timeout in seconds

        Returns:
            Metadata in the requested format

        Raises:
            DOIMetadataError: If metadata cannot be retrieved
        """
        headers = self._get_accept_header(format)

        try:
            response = requests.get(self.get_url(), headers=headers, timeout=timeout)
            response.raise_for_status()

            if format == "json":
                return response.json()
            else:
                return response.text

        except requests.RequestException as e:
            raise DOIMetadataError(
                f"Failed to retrieve metadata for DOI {self.doi}: {str(e)}"
            )

    def _get_accept_header(self, format: str) -> Dict[str, str]:
        """
        Get the appropriate Accept header for the requested format

        Args:
            format: Desired format

        Returns:
            Dictionary with Accept header
        """
        format_map = {
            "json": "application/vnd.citationstyles.csl+json",
            "bibtex": "application/x-bibtex",
            "ris": "application/x-research-info-systems",
            "crossref-xml": "application/vnd.crossref.unixref+xml",
            "datacite-xml": "application/vnd.datacite.datacite+xml",
            "rdf-xml": "application/rdf+xml",
            "turtle": "text/turtle",
        }

        accept = format_map.get(format.lower(), format)
        return {"Accept": accept}

    def get_crossref_metadata(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Get metadata from CrossRef API

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing CrossRef metadata

        Raises:
            DOIMetadataError: If metadata cannot be retrieved
        """
        url = f"{self.CROSSREF_API}/{self.doi}"

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {})
        except requests.RequestException as e:
            raise DOIMetadataError(
                f"Failed to retrieve CrossRef metadata for DOI {self.doi}: {str(e)}"
            )

    def get_datacite_metadata(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Get metadata from DataCite API

        Args:
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing DataCite metadata

        Raises:
            DOIMetadataError: If metadata cannot be retrieved
        """
        url = f"{self.DATACITE_API}/{self.doi}"

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except requests.RequestException as e:
            raise DOIMetadataError(
                f"Failed to retrieve DataCite metadata for DOI {self.doi}: {str(e)}"
            )

    def get_citation(self, style: str = "apa", timeout: int = 10) -> str:
        """
        Get a formatted citation for the DOI

        Args:
            style: Citation style (apa, mla, chicago, harvard, vancouver, etc.)
            timeout: Request timeout in seconds

        Returns:
            Formatted citation string

        Raises:
            DOIMetadataError: If citation cannot be retrieved
        """
        headers = {"Accept": f"text/x-bibliography; style={style}"}

        try:
            response = requests.get(self.get_url(), headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException as e:
            raise DOIMetadataError(
                f"Failed to retrieve citation for DOI {self.doi}: {str(e)}"
            )

    def get_abstract(
        self, source: Union[APISource, str] = APISource.AUTO, timeout: int = 10
    ) -> Optional[str]:
        """
        Get the abstract of the paper identified by the DOI

        Args:
            source: API source to use (APISource enum or string)
                   - APISource.AUTO or "auto": Try all sources (default)
                   - APISource.SEMANTIC_SCHOLAR or "semantic_scholar": Semantic Scholar only
                   - APISource.CROSSREF or "crossref": CrossRef only
                   - APISource.DATACITE or "datacite": DataCite only
                   - APISource.CSL_JSON or "csl_json": CSL-JSON only
            timeout: Request timeout in seconds

        Returns:
            Abstract text if available, None otherwise

        Raises:
            DOIMetadataError: If there's an error retrieving metadata
        """
        # Convert string to enum if necessary
        if isinstance(source, str):
            try:
                source = APISource(source.lower())
            except ValueError:
                source = APISource.AUTO

        # If AUTO, try all sources in order
        if source == APISource.AUTO:
            sources_to_try = [
                APISource.SEMANTIC_SCHOLAR,
                APISource.CROSSREF,
                APISource.DATACITE,
                APISource.CSL_JSON,
            ]
            for src in sources_to_try:
                abstract = self.get_abstract(source=src, timeout=timeout)
                if abstract:
                    return abstract
            return None

        # Try specific source
        if source == APISource.SEMANTIC_SCHOLAR:
            return self._get_abstract_semantic_scholar(timeout)
        elif source == APISource.CROSSREF:
            return self._get_abstract_crossref(timeout)
        elif source == APISource.DATACITE:
            return self._get_abstract_datacite(timeout)
        elif source == APISource.CSL_JSON:
            return self._get_abstract_csl_json(timeout)

        return None

    def _get_abstract_semantic_scholar(self, timeout: int) -> Optional[str]:
        """Get abstract from Semantic Scholar API"""
        try:
            semantic_scholar_url = (
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{self.doi}"
            )
            params = {"fields": "abstract"}
            headers = {"Accept": "application/json"}

            # Add API key to headers if provided
            if self.semantic_scholar_api_key:
                headers["x-api-key"] = self.semantic_scholar_api_key

            response = requests.get(
                semantic_scholar_url, params=params, headers=headers, timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                if "abstract" in data and data["abstract"]:
                    return data["abstract"].strip()
        except Exception:
            pass
        return None

    def _get_abstract_crossref(self, timeout: int) -> Optional[str]:
        """Get abstract from CrossRef API"""
        try:
            crossref_data = self.get_crossref_metadata(timeout=timeout)
            if "abstract" in crossref_data:
                abstract = crossref_data["abstract"]
                # CrossRef sometimes includes XML tags, clean them
                abstract = re.sub(r"<jats:.*?>", "", abstract)
                abstract = re.sub(r"</jats:.*?>", "", abstract)
                abstract = re.sub(r"<.*?>", "", abstract)
                return abstract.strip()
        except DOIMetadataError:
            pass
        return None

    def _get_abstract_datacite(self, timeout: int) -> Optional[str]:
        """Get abstract from DataCite API"""
        try:
            datacite_data = self.get_datacite_metadata(timeout=timeout)
            attributes = datacite_data.get("attributes", {})
            descriptions = attributes.get("descriptions", [])

            for desc in descriptions:
                if desc.get("descriptionType") == "Abstract":
                    return desc.get("description", "").strip()
        except DOIMetadataError:
            pass
        return None

    def _get_abstract_csl_json(self, timeout: int) -> Optional[str]:
        """Get abstract from CSL-JSON format"""
        try:
            csl_data = self.get_metadata(format="json", timeout=timeout)
            if "abstract" in csl_data:
                abstract = csl_data["abstract"]
                abstract = re.sub(r"<.*?>", "", abstract)
                return abstract.strip()
        except DOIMetadataError:
            pass
        return None

    def __str__(self) -> str:
        """String representation of the DOI"""
        return self.doi

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"DOI('{self.doi}')"

    def __eq__(self, other) -> bool:
        """Check equality with another DOI object"""
        if isinstance(other, DOI):
            return self.doi == other.doi
        return False

    def __hash__(self) -> int:
        """Make DOI objects hashable"""
        return hash(self.doi)
