# Academic Paper Reference Checker

A powerful Python tool for extracting and verifying references from academic papers in PDF format. Supports both single PDF processing and batch folder processing with comprehensive validation using DOI lookup and Semantic Scholar title-based search.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Features

### Core Capabilities
- **PDF Text Extraction**: Automatically extracts text from PDF files using PyMuPDF
- **Smart Reference Detection**: Identifies references section in academic papers
- **Multiple Citation Formats**: Supports numbered ([1], (1), 1.) and author-year citations
- **DOI Extraction**: Finds DOIs in multiple formats (doi:, https://doi.org/, direct format)
- **Title Extraction**: Extracts paper titles from references without DOIs

### Validation & Verification
- **Dual Validation Methods**:
  - **DOI-based**: Validates references using CrossRef API
  - **Title-based**: Searches papers by title using Semantic Scholar bulk API
- **Batch Processing**: Efficient batch API calls for multiple title searches
- **Comprehensive Coverage**: Checks ALL references, not just those with DOIs
- **Metadata Retrieval**: Fetches title, authors, and publication year
- **Confidence Scoring**: For title matches, provides high/medium/low confidence
- **Author Verification**: Matches author surnames for improved accuracy

### Processing Modes
- **Single PDF Mode**: Process one paper with detailed output
- **Batch Mode**: Process entire folders of PDFs
- **Automatic Detection**: Tool determines mode based on input path
- **Pattern Filtering**: Use glob patterns to filter PDFs in batch mode

### Reporting & Export
- **Detailed JSON Reports**: Complete validation results with metadata
- **Markdown Reports**: Human-readable formatted reports
- **Collective Summaries**: Batch mode generates overall statistics
- **Progress Tracking**: Real-time progress bars for long operations
- **Comprehensive Statistics**: Success rates, error tracking, and more

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Single PDF Mode](#single-pdf-mode)
  - [Batch Mode](#batch-mode)
  - [Command-Line Options](#command-line-options)
- [Configuration](#configuration)
- [Output Format](#output-format)
- [Examples](#examples)
- [API Keys](#api-keys)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Install Dependencies

1. **Clone or download this repository**

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install PyMuPDF requests python-dotenv tqdm
   ```

3. **Verify installation**:
   ```bash
   python ref-checker.py --help
   ```

### Optional: Set up API Key

For better performance and higher rate limits, set up a Semantic Scholar API key:

1. Get a free API key at https://www.semanticscholar.org/product/api
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your key:
   ```
   SEMANTIC_SCHOLAR_API_KEY=your_actual_api_key_here
   ```

**Rate Limits:**
- Without API key: 100 requests per 5 minutes
- With API key: 5,000 requests per 5 minutes

## ⚡ Quick Start

### Check a Single Paper
```bash
python ref-checker.py "paper.pdf"
```

### Process Multiple Papers
```bash
python ref-checker.py "papers_folder/"
```

### Save Results
```bash
# Single PDF with reports
python ref-checker.py paper.pdf -o results.json -m report.md

# Batch mode with output directory
python ref-checker.py papers/ -o reports/
```

## 📖 Usage

The tool automatically detects whether you're processing a single PDF or a folder.

### Single PDF Mode

Process one PDF file and get detailed results:

```bash
# Basic usage
python ref-checker.py "path/to/paper.pdf"

# With output files
python ref-checker.py paper.pdf -o results.json -m report.md

# Quiet mode (summary only)
python ref-checker.py paper.pdf -q

# Custom timeout for slow networks
python ref-checker.py paper.pdf --timeout 30
```

**Output:**
- Console summary with verification results
- Optional JSON file with complete data
- Optional Markdown report with formatted results

### Batch Mode

Process all PDFs in a folder:

```bash
# Process entire folder (auto-detected)
python ref-checker.py "papers/"

# Save reports to custom directory
python ref-checker.py papers/ -o reports/

# Filter by pattern
python ref-checker.py papers/ --pattern "*2023*.pdf"
python ref-checker.py papers/ --pattern "Smith*.pdf"

# Quiet mode
python ref-checker.py papers/ -q

# Force batch mode (if needed)
python ref-checker.py path/ --batch
```

**Output:**
- Individual JSON report for each PDF
- Individual Markdown report for each PDF
- `collective_report.json` - Overall statistics
- `collective_report.md` - Summary table with all PDFs

### Command-Line Options

```
usage: ref-checker.py [-h] [-o OUTPUT] [-m MARKDOWN] [-t TIMEOUT] [-q] 
                      [--api-key API_KEY] [--batch] [--pattern PATTERN] path

positional arguments:
  path                  Path to a PDF file or folder containing PDFs

options:
  -h, --help            Show this help message and exit
  -o, --output OUTPUT   Output file (single mode) or directory (batch mode)
  -m, --markdown MARKDOWN
                        Markdown report file (single mode only)
  -t, --timeout TIMEOUT
                        Timeout for API requests in seconds (default: 10)
  -q, --quiet           Quiet mode - minimal output
  --api-key API_KEY     Semantic Scholar API key for higher rate limits
  --batch               Force batch mode (auto-detected if path is directory)
  --pattern PATTERN     Glob pattern for PDFs in batch mode (default: *.pdf)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Semantic Scholar API Key (recommended)
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

### Rate Limiting

The tool automatically handles rate limiting:
- With API key: 0.5 second delay between requests (2 req/sec)
- Without API key: 2 second delay between requests (0.5 req/sec)
- Automatic backoff on 429 errors with exponential retry

## 📊 Output Format

### Single PDF Mode

**Console Output:**
```
Reading PDF: paper.pdf
✓ Found references section (5423 characters)
✓ Found 32 reference(s)
  - 28 with DOIs
  - 4 with titles (no DOI)
✓ Using Semantic Scholar API key

Processing 28 references with DOIs...
[1/28] Checking DOI: 10.1145/1234567.1234568
  ✓ VALID (DOI) - Paper Title Here
    Authors: Smith, J., Johnson, M.
    Year: 2020
...

Processing 4 references by title (batch mode)...
Checking references: 100%|████████████| 4/4 [00:05<00:00, 1.2s/ref]

======================================================================
REFERENCE CHECK SUMMARY
======================================================================
Total references found:        32
Valid DOI format:              28
Invalid DOI format:            0
References verified (exist):   30
References not found:          0
References with errors:        2
Success rate:                  93.8%
======================================================================
```

**JSON Output (`results.json`):**
```json
[
  {
    "doi": "10.1145/1234567.1234568",
    "title": "Paper Title Here",
    "authors": "Smith, J., Johnson, M., et al.",
    "year": 2020,
    "exists": true,
    "valid_format": true,
    "search_method": "doi",
    "raw_text": "Smith, J., Johnson, M. (2020). Paper Title..."
  },
  ...
]
```

### Batch Mode

**Collective Report (`collective_report.md`):**
```markdown
# Batch Reference Check Report

## Overall Summary

- **PDFs Processed:** 5
- **Successfully Processed:** 5
- **Failed:** 0
- **Total References:** 156
- **Verified References:** 142
- **Failed References:** 14
- **Overall Success Rate:** 91.0%

## Individual PDF Results

| PDF        | Status | References | Verified | Success Rate |
| ---------- | ------ | ---------- | -------- | ------------ |
| Paper1.pdf | ✓      | 32         | 30       | 93.8%        |
| Paper2.pdf | ✓      | 28         | 26       | 92.9%        |
...
```

## 💡 Examples

### Example 1: Single Paper Review

```bash
# Check references in a conference paper
python ref-checker.py "CHI2024_Submission.pdf" -o chi_results.json -m chi_report.md

# Review the markdown report
open chi_report.md  # macOS
# or: xdg-open chi_report.md  # Linux
```

### Example 2: Literature Review

```bash
# Process all papers from your literature review
python ref-checker.py "/path/to/literature_review/" -o review_reports/

# Check collective results
cat review_reports/collective_report.md
```

### Example 3: Conference Review

```bash
# Process papers from a specific conference/year
python ref-checker.py papers/ --pattern "*CHI2024*.pdf" -o chi2024_reports/

# Only 2023 papers
python ref-checker.py papers/ --pattern "*2023*.pdf" -o reports_2023/
```

### Example 4: Quick Check (Quiet Mode)

```bash
# Just want success rate, no detailed output
python ref-checker.py paper.pdf -q
```

### Example 5: Slow Network

```bash
# Increase timeout for slow/unreliable connections
python ref-checker.py paper.pdf --timeout 30
```

## 🔑 API Keys

### Semantic Scholar API

**Why you need it:**
- Public API: 100 requests per 5 minutes
- With key: 5,000 requests per 5 minutes
- Essential for papers with many references
- Faster processing in batch mode

**How to get:**
1. Visit https://www.semanticscholar.org/product/api
2. Sign up for a free account
3. Request an API key
4. Add to `.env` file

**Usage:**
```bash
# Via .env file (recommended)
echo "SEMANTIC_SCHOLAR_API_KEY=your_key" >> .env

# Or via command line
python ref-checker.py paper.pdf --api-key YOUR_KEY
```

## 🔧 Troubleshooting

### No References Found

**Problem:** `⚠ No references found in the document`

**Solutions:**
- Check if PDF has a "References" or "Bibliography" section
- Verify PDF text extraction: open PDF and try to select text
- Some PDFs are image-based - use OCR tools first
- Check section heading variations (References, REFERENCES, Bibliography)

### Rate Limit Errors

**Problem:** `429 Too Many Requests` or slow processing

**Solutions:**
- Add Semantic Scholar API key to `.env`
- Increase delay with `--timeout` option
- Process PDFs in smaller batches
- Wait a few minutes between large batches

### DOI Not Found

**Problem:** Many valid DOIs showing as "not found"

**Possible causes:**
- Temporary CrossRef API issues
- DOI is valid but paper not indexed
- Network connectivity issues
- DOI format extracted incorrectly

**Solutions:**
- Check the raw reference text in JSON output
- Try again later (API issues)
- Verify DOI manually at https://doi.org/
- Report extraction issues with example PDF

### Low Success Rate

**Problem:** Success rate below 70%

**Common causes:**
- References lack DOIs (older papers)
- Title extraction failed
- OCR errors in scanned PDFs
- Non-standard reference format

**Solutions:**
- Check `collective_report.md` to identify problem papers
- Review individual markdown reports for error patterns
- Consider manual verification for critical papers
- Report persistent issues with example PDFs

### Installation Issues

**Problem:** `ImportError` or module not found

**Solutions:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version (need 3.8+)
python --version

# Try with python3 explicitly
python3 ref-checker.py paper.pdf
```

## 🏗️ Architecture

### Project Structure

```
ref-checker/
├── ref-checker.py          # Main CLI entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Example configuration
├── README.md              # This file
│
├── ref_checker/           # Main package
│   ├── __init__.py       # Package exports
│   ├── __main__.py       # CLI implementation (single + batch)
│   ├── extractor.py      # PDF extraction & reference parsing
│   ├── checker.py        # DOI validation & title search
│   ├── reporter.py       # JSON & Markdown report generation
│   └── batch.py          # Batch processing logic
│
└── doi/                   # DOI handling library
    ├── api.py            # CrossRef API client
    ├── core.py           # DOI validation
    ├── query.py          # Semantic Scholar search
    └── batch.py          # Batch DOI operations
```

### Module Overview

**`extractor.py`** - Reference Extraction
- PDF text extraction with PyMuPDF
- References section detection
- DOI pattern matching
- Title extraction with multiple patterns
- Support for numbered and author-year citations
- Handling of multi-word surnames (Van den Bogaert, de la Cruz)

**`checker.py`** - Reference Verification
- DOI validation via CrossRef
- Title-based search via Semantic Scholar
- Batch processing with rate limiting
- Author surname matching
- Confidence scoring for title matches
- Intelligent scoring system (title + author + year + citations)

**`reporter.py`** - Report Generation
- JSON export with complete metadata
- Markdown report formatting
- Grouping by verification status
- Collapsible sections for errors
- Summary statistics

**`batch.py`** - Batch Processing
- Folder scanning with pattern matching
- Progress tracking
- Individual report generation
- Collective summary reports
- Error handling and recovery

### Key Algorithms

**Reference Splitting:**
- Numbered format: `[1]`, `(1)`, `1.`
- Author-year format: `Surname, I., Year.`
- Multi-word surnames: `(?:\s+[a-z]+)*` for "van", "de", etc.

**DOI Cleaning:**
- Remove line breaks and spaces
- Strip trailing text after DOI
- Preserve hyphens in identifiers (978-3-030)
- Handle nested parentheses

**Title Matching Scoring:**
- Title similarity: 0-100 points
- Author match: +30 points
- Year proximity: 0-20 points (±2 years)
- Citation count: 0-10 points
- Threshold: High (≥120), Medium (≥90), Low (≥70)

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

Found a bug or have a feature request? Please open an issue with:
- Description of the problem
- Example PDF (if applicable)
- Expected vs. actual behavior
- Error messages or logs

### Feature Requests

Ideas for improvements:
- Support for additional citation formats
- New export formats (CSV, Excel)
- Web interface
- Parallel processing
- Additional metadata fields

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PyMuPDF (fitz)** - PDF text extraction
- **CrossRef API** - DOI validation and metadata
- **Semantic Scholar API** - Title-based paper search
- **tqdm** - Progress bars

## 📞 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## 🔄 Version History

### Current Version
- ✅ Single PDF and batch folder processing
- ✅ Automatic mode detection
- ✅ DOI and title-based verification
- ✅ Multi-word surname support
- ✅ Comprehensive reporting
- ✅ Rate limiting and error handling

### Recent Improvements
- Fixed multi-word surname splitting
- Improved DOI hyphen preservation (978-3-030)
- Enhanced title extraction patterns
- Added collective batch reports
- Unified CLI interface

## 📚 Additional Resources

- [Semantic Scholar API Documentation](https://api.semanticscholar.org/)
- [CrossRef API Documentation](https://www.crossref.org/documentation/retrieve-metadata/)
- [DOI System](https://www.doi.org/)

---

**Made with ❤️ for researchers and academics**
