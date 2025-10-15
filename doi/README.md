# DOI Library

A Python library for interacting with DOI (Digital Object Identifier) REST APIs.

## Features

- ✅ Resolve DOIs to their target URLs
- ✅ Retrieve metadata in multiple formats (JSON, BibTeX, RIS, XML, etc.)
- ✅ Get formatted citations in various styles (APA, MLA, Chicago, etc.)
- ✅ **Get paper abstracts** from DOI metadata
- ✅ **Batch process multiple DOIs** with rate limiting ✨NEW!
- ✅ **Export results to JSON or CSV** ✨NEW!
- ✅ Query CrossRef and DataCite APIs
- ✅ Search for DOIs
- ✅ Validate DOI format
- ✅ Simple, intuitive API

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from doi import DOI, search_dois, validate_doi

# Create a DOI object
doi = DOI("10.1371/journal.pone.0000000")

# Resolve DOI to target URL
url = doi.resolve()
print(url)

# Get metadata in JSON format
metadata = doi.get_metadata(format="json")
print(metadata)

# Get a formatted citation
citation = doi.get_citation(style="apa")
print(citation)

# Get BibTeX entry
bibtex = doi.get_metadata(format="bibtex")
print(bibtex)
```

## Usage Examples

### Working with DOI Objects

```python
from doi import DOI

# Initialize with various formats
doi1 = DOI("10.1234/example")
doi2 = DOI("doi:10.1234/example")
doi3 = DOI("https://doi.org/10.1234/example")

# All are normalized to the same format
print(doi1.doi)  # "10.1234/example"
print(doi2.doi)  # "10.1234/example"
print(doi3.doi)  # "10.1234/example"

# Validate DOI format
if doi1.is_valid():
    print("Valid DOI!")

# Get the full DOI URL
print(doi1.get_url())  # "https://doi.org/10.1234/example"
```

### Resolving DOIs

```python
from doi import DOI, resolve_doi

# Using DOI object
doi = DOI("10.1371/journal.pone.0000000")
target_url = doi.resolve()
print(f"DOI resolves to: {target_url}")

# Using convenience function
target_url = resolve_doi("10.1371/journal.pone.0000000")
```

### Getting Metadata

```python
from doi import DOI

doi = DOI("10.1371/journal.pone.0000000")

# Get JSON metadata (CSL-JSON format)
json_metadata = doi.get_metadata(format="json")

# Get BibTeX
bibtex = doi.get_metadata(format="bibtex")

# Get RIS
ris = doi.get_metadata(format="ris")

# Get CrossRef metadata
crossref_data = doi.get_crossref_metadata()
print(f"Title: {crossref_data.get('title', ['N/A'])[0]}")
print(f"Authors: {crossref_data.get('author', [])}")

# Get DataCite metadata
datacite_data = doi.get_datacite_metadata()
```

### Getting Citations

```python
from doi import DOI, get_doi_citation

doi = DOI("10.1371/journal.pone.0000000")

# Get citation in different styles
apa = doi.get_citation(style="apa")
mla = doi.get_citation(style="mla")
chicago = doi.get_citation(style="chicago-author-date")
harvard = doi.get_citation(style="harvard3")
vancouver = doi.get_citation(style="vancouver")

print("APA:", apa)
print("MLA:", mla)

# Using convenience function
citation = get_doi_citation("10.1371/journal.pone.0000000", style="apa")
```

### Getting Paper Abstracts

**Now supports ACM, IEEE, and many other publishers!** ✨

```python
from doi import DOI, get_doi_abstract

# Using DOI object - works with ACM DOIs!
doi = DOI("10.1145/3706598.3715579")  # ACM CHI paper
abstract = doi.get_abstract()

if abstract:
    print("Abstract:")
    print(abstract)
else:
    print("Abstract not available")

# Also works with other publishers
science_doi = DOI("10.1126/science.1249098")
ieee_doi = DOI("10.1109/5.771073")

# Using convenience function
abstract = get_doi_abstract("10.1145/3544548.3580672")  # ACM paper

# Get abstract with other metadata
doi = DOI("10.1145/3706598.3715579")
metadata = doi.get_crossref_metadata()
abstract = doi.get_abstract()

print(f"Title: {metadata.get('title', ['N/A'])[0]}")
print(f"Abstract: {abstract if abstract else 'Not available'}")
```

**Supported Publishers:**
- ✅ ACM (Association for Computing Machinery)
- ✅ IEEE (Institute of Electrical and Electronics Engineers)
- ✅ Nature, Science, PLOS, and many more via Semantic Scholar API

### Batch Processing Multiple DOIs

**NEW!** Process multiple DOIs with rate limiting and save to JSON/CSV:

```python
from doi import DOIBatch

# List of DOIs to process
dois = [
    "10.1145/3706598.3715579",
    "10.1126/science.1249098",
    "10.1038/nature12373",
]

# Create batch processor with 1 second rate limit
batch = DOIBatch(rate_limit=1.0)

# Specify fields to retrieve
fields = ['doi', 'title', 'abstract', 'authors', 'year', 'publisher']

# Process all DOIs
results = batch.process_dois(dois, fields=fields, verbose=True)

# Save to JSON
batch.save_to_json('results.json')

# Save to CSV
batch.save_to_csv('results.csv', fields=fields)

# Check for errors
if batch.get_errors():
    print(f"Failed: {len(batch.get_errors())} DOIs")

# Convenience functions
from doi import process_dois_to_json, process_dois_to_csv

process_dois_to_json(dois, 'quick_results.json', rate_limit=1.0)
process_dois_to_csv(dois, 'quick_results.csv', rate_limit=1.0)
```

**Available Fields:**
- `title`, `abstract`, `authors`, `year`, `publisher`, `journal`, `doi`, `url`, `type`, `citations`

**Rate Limiting Recommendations:**
- `rate_limit=0.5` - 2 requests/second (for small batches)
- `rate_limit=1.0` - 1 request/second (recommended)
- `rate_limit=2.0` - 1 request/2 seconds (very polite)

### Searching for DOIs

```python
from doi import DOIQuery, search_dois

# Using DOIQuery class
query = DOIQuery(mailto="your.email@example.com")  # Polite API access
results = query.search("machine learning", rows=10)

for item in results["message"]["items"]:
    print(f"DOI: {item['DOI']}")
    print(f"Title: {item.get('title', ['N/A'])[0]}")
    print()

# Using convenience function
results = search_dois("climate change", rows=5, mailto="your.email@example.com")
for item in results:
    print(f"{item['DOI']}: {item.get('title', ['N/A'])[0]}")
```

### Filtering DOIs

```python
from doi import DOIQuery

query = DOIQuery(mailto="your.email@example.com")

# Filter by type
results = query.filter(
    filters={"type": "journal-article"},
    rows=10
)

# Multiple filters
results = query.filter(
    filters={
        "type": "journal-article",
        "from-pub-date": "2023-01-01",
        "until-pub-date": "2023-12-31"
    },
    rows=20
)
```

### Validating DOIs

```python
from doi import validate_doi, DOI, DOIValidationError

# Using convenience function
if validate_doi("10.1234/example"):
    print("Valid DOI format")
else:
    print("Invalid DOI format")

# Using DOI class with validation
try:
    doi = DOI("invalid-doi", validate=True)
except DOIValidationError as e:
    print(f"Error: {e}")

# Disable validation
doi = DOI("invalid-doi", validate=False)
print(doi.is_valid())  # False
```

### Error Handling

```python
from doi import DOI, DOIResolutionError, DOIMetadataError

doi = DOI("10.1234/nonexistent")

# Handle resolution errors
try:
    url = doi.resolve()
except DOIResolutionError as e:
    print(f"Failed to resolve: {e}")

# Handle metadata errors
try:
    metadata = doi.get_metadata()
except DOIMetadataError as e:
    print(f"Failed to get metadata: {e}")
```

## API Reference

### DOI Class

#### `DOI(doi: str, validate: bool = True)`
Create a DOI object.

**Methods:**
- `is_valid() -> bool`: Check if DOI format is valid
- `get_url() -> str`: Get full DOI URL
- `resolve(timeout: int = 10) -> str`: Resolve to target URL
- `get_metadata(format: str = "json", timeout: int = 10) -> Any`: Get metadata
- `get_crossref_metadata(timeout: int = 10) -> Dict`: Get CrossRef metadata
- `get_datacite_metadata(timeout: int = 10) -> Dict`: Get DataCite metadata
- `get_citation(style: str = "apa", timeout: int = 10) -> str`: Get formatted citation
- `get_abstract(timeout: int = 10) -> Optional[str]`: Get paper abstract

### DOIQuery Class

#### `DOIQuery(mailto: Optional[str] = None)`
Query DOI databases (primarily CrossRef).

**Methods:**
- `search(query: str, rows: int = 20, ...) -> Dict`: Search for DOIs
- `filter(filters: Dict, rows: int = 20, ...) -> Dict`: Filter DOIs

### Convenience Functions

- `resolve_doi(doi: str, timeout: int = 10) -> str`
- `get_doi_metadata(doi: str, format: str = "json", timeout: int = 10) -> Any`
- `get_doi_citation(doi: str, style: str = "apa", timeout: int = 10) -> str`
- `get_doi_abstract(doi: str, timeout: int = 10) -> Optional[str]`
- `validate_doi(doi: str) -> bool`
- `search_dois(query: str, rows: int = 20, mailto: Optional[str] = None) -> List`

### Supported Metadata Formats

- `json`: CSL-JSON format
- `bibtex`: BibTeX format
- `ris`: RIS format
- `crossref-xml`: CrossRef XML
- `datacite-xml`: DataCite XML
- `rdf-xml`: RDF/XML format
- `turtle`: Turtle format

### Supported Citation Styles

Common styles include: `apa`, `mla`, `chicago-author-date`, `harvard3`, `vancouver`, `ieee`, `nature`, `science`, and many more.

## Exception Hierarchy

```
DOIError (base exception)
├── DOIValidationError
├── DOIResolutionError
└── DOIMetadataError
```

## API Services Used

- **doi.org**: DOI resolution and content negotiation
- **CrossRef API**: Bibliographic metadata for scholarly content
- **DataCite API**: Metadata for research data and other resources

## Best Practices

1. **Use polite API access**: Provide your email when using `DOIQuery`
   ```python
   query = DOIQuery(mailto="your.email@example.com")
   ```

2. **Handle exceptions**: Always wrap API calls in try-except blocks
   ```python
   try:
       metadata = doi.get_metadata()
   except DOIMetadataError as e:
       print(f"Error: {e}")
   ```

3. **Validate DOIs**: Check format before making API calls
   ```python
   if doi.is_valid():
       metadata = doi.get_metadata()
   ```

4. **Set appropriate timeouts**: Adjust timeout based on your needs
   ```python
   doi.resolve(timeout=30)  # 30 second timeout
   ```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
