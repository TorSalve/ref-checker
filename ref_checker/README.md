# ref_checker Package

A well-organized Python package for extracting and verifying academic paper references from PDF files.

## Package Structure

```
ref_checker/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── extractor.py         # PDF extraction and reference parsing
├── checker.py           # Reference validation and verification
└── reporter.py          # Report generation (JSON and Markdown)
```

## Modules

### `extractor.py`
Contains the `ReferenceExtractor` class for:
- PDF text extraction using PyMuPDF
- References section detection
- Individual reference parsing
- DOI and title extraction
- Author and year extraction
- Handling merged references and formatting issues

### `checker.py`
Contains the `ReferenceChecker` class for:
- DOI validation via CrossRef API
- Title-based search via Semantic Scholar API
- Multi-result evaluation with intelligent scoring
- Author verification
- Batch processing with rate limiting
- Retry logic with exponential backoff

### `reporter.py`
Contains the `ReportGenerator` class for:
- Summary statistics generation
- JSON output with detailed results
- Markdown reports grouped by confidence level
- Human-readable formatting

### `__main__.py`
CLI entry point with:
- Argument parsing
- Environment variable loading
- Workflow orchestration
- Error handling

## Usage

### As a package:
```python
from ref_checker import ReferenceExtractor, ReferenceChecker, ReportGenerator

# Extract references
extractor = ReferenceExtractor("paper.pdf")
references = extractor.extract_references()

# Check references
checker = ReferenceChecker(semantic_scholar_api_key="YOUR_KEY")
results = checker.check_references(references)

# Generate reports
reporter = ReportGenerator(results)
reporter.save_json("output.json")
reporter.save_markdown("report.md")
```

### From command line:
```bash
python ref-checker.py paper.pdf -o output.json -m report.md
```

Or run as a module:
```bash
python -m ref_checker paper.pdf -o output.json -m report.md
```

## Features

- **PDF Extraction**: Robust text extraction with reference section detection
- **Reference Parsing**: Advanced parsing handling multiple citation formats
- **DOI Validation**: Direct validation via CrossRef API
- **Title Search**: Semantic Scholar integration with bulk API
- **Multi-Result Evaluation**: Scores top 5 search results using intelligent algorithm
- **Scoring System**: 160-point system combining:
  - Title similarity (0-100 points)
  - Author matching (30 points)
  - Year proximity (0-20 points)
  - Citation count (0-10 points)
- **Confidence Levels**: High (≥120), Medium (90-119), Low (70-89)
- **Author Verification**: Rejects mismatched authors to prevent false positives
- **Rate Limiting**: Intelligent delays and exponential backoff
- **Progress Tracking**: tqdm progress bars for batch operations
- **Flexible Output**: JSON and Markdown reports

## Dependencies

- PyMuPDF (fitz): PDF text extraction
- python-dotenv: Environment variable management
- requests: HTTP API calls
- tqdm: Progress bars
- doi library: DOI validation and Semantic Scholar integration

## API Keys

For better rate limits, set your Semantic Scholar API key:
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
```

Or add to `.env` file:
```
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

## Improvements Over Original Code

1. **Modular Structure**: Separated concerns into distinct modules
2. **Reusable Components**: Classes can be imported and used independently
3. **Better Maintainability**: Each module has a single responsibility
4. **Clearer Dependencies**: Import structure shows relationships
5. **Easier Testing**: Modules can be tested in isolation
6. **Documentation**: Each module and class is well-documented
7. **Type Hints**: Preserved throughout for better IDE support

## Version

1.0.0 - Initial refactored release
