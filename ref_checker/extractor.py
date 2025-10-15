"""
Reference extraction from academic papers in PDF format.

This module handles PDF text extraction and parsing of reference sections.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError(
        "PyMuPDF is not installed. Please install it with: pip install PyMuPDF"
    )


class ReferenceExtractor:
    """Extract references from academic papers in PDF format"""

    def __init__(self, pdf_path: str):
        """
        Initialize the reference extractor

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def extract_text(self) -> str:
        """
        Extract all text from the PDF

        Returns:
            Full text content of the PDF
        """
        try:
            doc = fitz.open(self.pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise RuntimeError(f"Error reading PDF: {e}")

    def find_references_section(self, text: str) -> Optional[str]:
        """
        Find and extract the references section from the paper text

        Args:
            text: Full text of the paper

        Returns:
            Text of the references section, or None if not found
        """
        # Common reference section headers
        patterns = [
            r"\nREFERENCES\s*\n",
            r"\nReferences\s*\n",
            r"\nBIBLIOGRAPHY\s*\n",
            r"\nBibliography\s*\n",
            r"\nWorks Cited\s*\n",
            r"\nLiterature\s*\n",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract everything after the references header
                refs_start = match.end()
                # Try to find end of references (e.g., appendix, acknowledgments)
                end_patterns = [
                    r"\n(APPENDIX|Appendix|ACKNOWLEDGMENTS|Acknowledgments|ACKNOWLEDGEMENTS|Acknowledgements)\s*\n"
                ]
                refs_end = len(text)
                for end_pattern in end_patterns:
                    end_match = re.search(end_pattern, text[refs_start:])
                    if end_match:
                        refs_end = refs_start + end_match.start()
                        break

                return text[refs_start:refs_end]

        return None

    def extract_dois_from_text(self, text: str) -> List[str]:
        """
        Extract DOI strings from text

        Args:
            text: Text to search for DOIs

        Returns:
            List of DOI strings found
        """
        # DOI patterns
        doi_patterns = [
            r"doi:\s*([^\s\]]+)",  # doi: 10.xxxx/yyyy
            r"DOI:\s*([^\s\]]+)",  # DOI: 10.xxxx/yyyy
            r"https?://doi\.org/([^\s\]]+)",  # https://doi.org/10.xxxx/yyyy
            r"https?://dx\.doi\.org/([^\s\]]+)",  # http://dx.doi.org/10.xxxx/yyyy
            r"\b(10\.\d{4,}/[^\s\]]+)",  # Direct DOI format
        ]

        dois = []
        for pattern in doi_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                doi = match.group(1)
                # Clean up common trailing characters
                doi = re.sub(r"[\.,;\)\]]+$", "", doi)
                dois.append(doi)

        # Remove duplicates while preserving order
        seen = set()
        unique_dois = []
        for doi in dois:
            if doi not in seen:
                seen.add(doi)
                unique_dois.append(doi)

        return unique_dois

    def parse_individual_references(
        self, refs_text: str
    ) -> List[Dict[str, Optional[str]]]:
        """
        Parse individual reference entries from the references section

        Args:
            refs_text: Text of the references section

        Returns:
            List of dictionaries with parsed reference information
        """
        references = []

        # Detect citation format: numbered vs author-year
        # Check if we have numbered references like [1], (1), 1.
        # Must be followed by capital letter to be a real reference number (not a page number)
        has_numbered_refs = bool(
            re.search(r"\n\s*(?:\[\d+\]|\(\d+\)|\d{1,3}\.)\s+[A-Z]", refs_text)
        )

        # Check if we have author-year format: "Lastname, I., Year." or "Lastname, I.I., Year."
        # Also matches multi-word names: "Van den Bogaert, L., Year."
        # Note: The pattern looks for comma BEFORE year, not period
        has_authoryear_refs = bool(
            re.search(
                r"\n[A-Z][a-z]+(?:\s+[a-z]+)*(?:-[A-Z][a-z]+)?,\s+[A-Z]\.(?:[A-Z]\.)*,\s+\d{4}\.",
                refs_text,
            )
        )

        if has_authoryear_refs and not has_numbered_refs:
            # Author-year format: split on "Lastname, Initial(s)..." at start of line
            # Pattern: Newline followed by author name (use lookahead to preserve the match)
            # Matches: "Brown, R.W., 1957" or "Corniani, G., Saal, H.P., 2020" (multiple authors)
            # Also matches multi-word names: "Van den Bogaert, L." or "de la Cruz, M."
            # Pattern breakdown:
            #   [A-Z][a-z]+ - First capitalized word (Van, Brown, etc.)
            #   (?:\s+[a-z]+)* - Zero or more lowercase words (den, de, la, etc.)
            #   (?:-[A-Z][a-z]+)? - Optional hyphenated part (for names like "Müller-Lyer")
            #   ,\s+[A-Z]\. - Comma + initial
            pattern = r"\n(?=[A-Z][a-z]+(?:\s+[a-z]+)*(?:-[A-Z][a-z]+)?,\s+[A-Z]\.)"
            parts = re.split(pattern, refs_text)
        else:
            # Numbered format: split by common reference numbering patterns
            # Matches: [1], [2], (1), (2), 1., 2., etc. at the start of a line
            # IMPORTANT: For plain numbers (e.g., "1."), only match 1-3 digits to avoid
            # matching years like "2021." which are 4 digits
            pattern = r"\n\s*(?:\[\d+\]|\(\d+\)|\d{1,3}\.)\s+"
            parts = re.split(pattern, refs_text)

        # Remove empty parts and join multi-line references
        ref_texts = []
        for part in parts:
            part = part.strip()
            if part:
                # Fix hyphenation at line breaks (e.g., "Sum- mary" → "Summary")
                # BUT preserve hyphens in DOIs and ISBNs (e.g., "978-3" should stay "978-3")
                # Strategy: Only remove hyphen if it's between letters (word hyphenation)
                # Keep hyphen if between digits or in patterns like "978-"
                part = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", part, flags=re.IGNORECASE)

                # Clean up the reference text by normalizing whitespace
                # Replace multiple spaces/newlines with single space
                cleaned = re.sub(r"\s+", " ", part)

                # Remove invisible Unicode characters (zero-width spaces, etc.) that PDFs insert
                # These can appear anywhere and break DOI extraction
                cleaned = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", cleaned)

                # Remove page headers/footers that get mixed into references
                # Pattern: "Scientific Reports | (2025) 15:10297 7 | https://doi.org/..."
                # These typically have: JournalName | (YEAR) Volume:Page | URL
                cleaned = re.sub(
                    r"\b(?:Scientific Reports|Nature|Science|Cell|PNAS|Proceedings|Journal)[^\|]*\|\s*\(\d{4}\)\s*\d+[:\d\s]*\|\s*https?://[^\s]+",
                    "",
                    cleaned,
                    flags=re.IGNORECASE,
                )

                # Fix DOIs split by spaces or invisible characters
                # 1. "https: //doi.org" → "https://doi.org"
                cleaned = re.sub(
                    r"https?\s*:\s*//", "https://", cleaned, flags=re.IGNORECASE
                )
                # 2. "doi.org/10.1234/ 5678" → "doi.org/10.1234/5678"
                cleaned = re.sub(
                    r"(doi\.org/\S+?)\s+(\d+)", r"\1\2", cleaned, flags=re.IGNORECASE
                )
                # 3. "10.1109/VR.2019. 8797975" → "10.1109/VR.2019.8797975"
                cleaned = re.sub(r"(10\.\d{4,}[./]\S+?)\s+(\d+)", r"\1\2", cleaned)

                # 4. More aggressive: Remove ALL spaces within DOI strings
                # Pattern: "doi.org/10. 1234 / 5678" → "doi.org/10.1234/5678"
                def clean_doi_spaces(match):
                    doi_full = match.group(0)
                    # Remove all spaces from the DOI portion
                    return re.sub(r"\s+", "", doi_full)

                cleaned = re.sub(
                    r"(?:https?://)?doi\.org/10\.[^\s]{1,}(?:\s+[^\s]+)*",
                    clean_doi_spaces,
                    cleaned,
                    flags=re.IGNORECASE,
                )

                # Remove conference header/footer contamination
                # Pattern: "Conference Year, Date range, Location AuthorNames"
                # E.g., "VRST '21, December 8–10, 2021, Osaka, Japan Tor-Salve Dalsgaard"
                # This typically appears between the publication info and DOI
                cleaned = self._remove_conference_header_contamination(cleaned)

                ref_texts.append(cleaned)

        for ref_text in ref_texts:
            # Skip if this looks like just a continuation line or too short
            if len(ref_text) < 20:
                continue

            # Skip if it's just author names (no year or DOI)
            if (
                not re.search(r"\b(19|20)\d{2}\b", ref_text)
                and "doi.org" not in ref_text.lower()
            ):
                continue

            # Check if this reference might contain multiple merged references
            # Indicators: multiple DOIs, or multiple year patterns with author patterns between them
            split_refs = self._split_merged_references(ref_text)

            for split_ref in split_refs:
                # Extract DOI if present - look for complete DOI
                doi = self._extract_complete_doi(split_ref)

                # Extract title (usually in quotes or italics, or between author and publication info)
                title = self._extract_title_from_reference(split_ref)

                # Extract year
                year = self._extract_year_from_reference(split_ref)

                references.append(
                    {"raw_text": split_ref, "doi": doi, "title": title, "year": year}
                )

        return references

    def _remove_conference_header_contamination(self, ref_text: str) -> str:
        """
        Remove conference header/footer text that gets mixed into references

        Args:
            ref_text: Reference text that might contain header contamination

        Returns:
            Cleaned reference text
        """
        # Pattern to detect conference header contamination:
        # "ConferenceName 'YY, Month Day–Day, Year, Location FirstName LastName, FirstName LastName"
        # This appears between publication venue and DOI/end

        # Look for pattern: Conference/Journal abbreviation followed by year with apostrophe,
        # date range, location, then author names (which shouldn't be there)
        # E.g., "VRST '21, December 8–10, 2021, Osaka, Japan Tor-Salve Dalsgaard, Jarrod Knibbe"

        contamination_patterns = [
            # Pattern 1: "CONF 'YY, Month DD-DD, YYYY, Location AuthorNames..."
            r"([A-Z]{2,6}\s+'?\d{2},?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}[–-]\d{1,2},?\s+\d{4},?\s+[A-Z][a-z]+,?\s+[A-Z][a-z]+)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+(?:,\s+[A-Z][a-z]+\s+[A-Z][a-z]+)+)",
            # Pattern 2: Similar but without date range
            r"([A-Z]{2,6}\s+'?\d{2},?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4},?\s+[A-Z][a-z]+,?\s+[A-Z][a-z]+)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+(?:,\s+[A-Z][a-z]+\s+[A-Z][a-z]+)+)",
        ]

        for pattern in contamination_patterns:
            match = re.search(pattern, ref_text)
            if match:
                # Remove the author names part (group 2) but keep the venue/date info
                # Actually, let's remove the entire contaminated section if it appears after a journal/proceedings
                # and before a DOI or at the end

                # Check if this appears in a suspicious location (between "Proceedings/Journal" and "https://doi")
                contamination_start = match.start()
                contamination_end = match.end()

                # Look for DOI or end of string after this point
                after_contamination = ref_text[contamination_end:]

                # If there's a DOI soon after, or if we're near the end, remove the entire match
                if (
                    re.search(
                        r"^\s*(?:Symposium|Conference|Proceedings)",
                        after_contamination,
                        re.IGNORECASE,
                    )
                    or re.search(
                        r"https?://doi\.org", after_contamination, re.IGNORECASE
                    )
                    or len(after_contamination) < 50
                ):
                    # Remove the contamination
                    ref_text = ref_text[:contamination_start] + after_contamination

        return ref_text

    def _split_merged_references(self, ref_text: str) -> List[str]:
        """
        Detect and split references that have been merged together

        Args:
            ref_text: Reference text that might contain multiple merged references

        Returns:
            List of individual reference texts (single item if not merged)
        """
        # Strategy: Look for patterns that indicate a new reference starting mid-text
        # Common indicators:
        # 1. Multiple DOIs (most reliable)
        # 2. Pattern like: "Journal YEAR (YEAR), pages. https://doi.org/... AuthorName. YEAR."
        #    where we have two different years with author names between them

        # Check for multiple DOIs
        doi_matches = list(
            re.finditer(r"https?://doi\.org/\S+", ref_text, re.IGNORECASE)
        )
        if len(doi_matches) > 1:
            # Split at the start of the second DOI, working backwards to find logical split point
            second_doi_pos = doi_matches[1].start()

            # Look backwards from second DOI to find author pattern (capitalized names)
            # Pattern: "Full Journal Name. Author1, Author2, and Author3"
            before_second_doi = ref_text[:second_doi_pos]

            # Try to find where the new reference starts (look for ". " followed by capitalized word)
            # This usually indicates end of previous reference and start of new author list
            potential_splits = list(
                re.finditer(r"\.\s+([A-Z][a-z]+\s+[A-Z])", before_second_doi)
            )

            if potential_splits:
                # Take the last occurrence before the second DOI
                split_point = potential_splits[-1].start() + 1  # After the period
                ref1 = ref_text[:split_point].strip()
                ref2 = ref_text[split_point:].strip()

                # Extract years from both parts
                year1_match = re.search(r"\b(19|20)\d{2}\b", ref1)
                year2_match = re.search(r"\b(19|20)\d{2}\b", ref2)

                # Validate both parts have years AND different years
                # IMPORTANT: If both years are the same, this is likely ONE reference with duplicate DOI
                # (e.g., "...doi.org/10.1234 arXiv:doi.org/10.1234")
                if (
                    year1_match
                    and year2_match
                    and year1_match.group(0) != year2_match.group(0)
                ):
                    return [ref1, ref2]

        # Check for DOI followed by text that looks like a new reference
        # Pattern: "...https://doi.org/XXXXX Title/Conference Year Author Names"
        # Look for: DOI, then later there's "Author1, Author2" or "Author1 Author2. Year"
        doi_match = re.search(r"https?://doi\.org/\S+", ref_text, re.IGNORECASE)
        if doi_match:
            after_doi = ref_text[doi_match.end() :]

            # Look for pattern: venue/journal/conference name followed by author-like text
            # E.g., "VRST '21, December 8–10, 2021, Osaka, Japan Tor-Salve Dalsgaard, Jarrod Knibbe"
            # Pattern: Location/Date, then FirstName LastName, FirstName LastName
            venue_author_pattern = r"([A-Z][a-z]+(?:\s+\d+)?[,.]?\s+(?:December|January|February|March|April|May|June|July|August|September|October|November)?\s*\d{1,2}[–-]\d{1,2},?\s+\d{4},?\s+[A-Z][a-z]+,?\s+[A-Z][a-z]+)\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?\s+[A-Z][a-z]+,\s+[A-Z][a-z]+\s+[A-Z][a-z]+)"

            match = re.search(venue_author_pattern, after_doi)
            if match:
                # Split after the venue/location part, before author names
                split_pos = doi_match.end() + match.start(2)
                ref1 = ref_text[:split_pos].strip()
                ref2 = ref_text[split_pos:].strip()

                if len(ref1) > 30 and len(ref2) > 30:
                    return [ref1, ref2]

        # Check for pattern: year and page numbers, followed by author names and another year
        # Example: "Journal (2008), 43–46. https://doi.org/... FirstName LastName. 2021."
        pattern = r"(\b(19|20)\d{2}\b.*?(?:https?://doi\.org/\S+|doi:\s*\S+))\s+([A-Z][a-z]+\s+[A-Z][a-z]+.*?\b(19|20)\d{2}\b)"
        match = re.search(pattern, ref_text, re.IGNORECASE)

        if match:
            # Find the split point between the DOI/first year and the new author names
            first_ref_end = match.start(3)  # Where the new author names start

            # Look backwards to find a good split point (period or comma)
            split_text = ref_text[:first_ref_end]
            last_period = split_text.rfind(".")

            if last_period > len(ref_text) * 0.3:  # Make sure it's not too early
                ref1 = ref_text[: last_period + 1].strip()
                ref2 = ref_text[last_period + 1 :].strip()

                # Extract years from both parts
                year1_match = re.search(r"\b(19|20)\d{2}\b", ref1)
                year2_match = re.search(r"\b(19|20)\d{2}\b", ref2)

                # Validate both parts
                # IMPORTANT: If both years are the same, this is likely ONE reference
                # (e.g., "Author. 1997. Title. Journal (1997), pages.")
                if (
                    len(ref1) > 30
                    and len(ref2) > 30
                    and year1_match
                    and year2_match
                    and year1_match.group(0) != year2_match.group(0)  # Different years
                ):
                    return [ref1, ref2]

        # No merge detected, return as single reference
        return [ref_text]

    def _extract_complete_doi(self, ref_text: str) -> Optional[str]:
        """
        Extract the complete DOI from reference text, handling multi-line DOIs

        Args:
            ref_text: Raw reference text (already normalized)

        Returns:
            Complete DOI string or None
        """
        # Pattern for DOI - capture everything after doi.org/ or doi:
        # More permissive pattern to capture complete DOI
        doi_patterns = [
            r"https?://doi\.org/(10\.[^\s]+)",  # URL format
            r"doi\.org/(10\.[^\s]+)",  # Without http
            r"doi:\s*(10\.[^\s]+)",  # doi: prefix
            r"\b(10\.\d{4,}(?:\.\d+)*\/[^\s]+)",  # Raw DOI format
        ]

        for pattern in doi_patterns:
            match = re.search(pattern, ref_text, re.IGNORECASE)
            if match:
                doi = match.group(1)

                # Remove all whitespace characters (including zero-width spaces, invisible chars)
                # DOIs should never contain spaces
                doi = re.sub(r"\s+", "", doi)

                # Remove invisible Unicode characters that PDFs sometimes insert
                # This includes zero-width spaces (\u200b), zero-width joiners, etc.
                doi = re.sub(r"[\u200b-\u200f\u2028-\u202f\ufeff]", "", doi)

                # Clean up trailing content that's not part of DOI:
                # - Year in parentheses at END: (1977), (2020) - but NOT parentheses within DOI like 10.1016/0031-9384(86)90050-8
                # - Publisher text after DOI: (AssociationforComputingMachinery...)
                # - Trailing URLs like ".www.nature.com/scientificreports/"
                # Strategy: Remove trailing parenthetical that contains only digits (year) or text (publisher)
                # but keep parentheses that are part of the DOI structure

                # First, remove trailing year like "(1977)" or "(2020)" and anything after it
                # Pattern: (YEAR) followed by anything that's not part of DOI (not digit/slash)
                doi = re.sub(r"\((\d{4})\)(?:[^0-9/].*)?$", "", doi)

                # Then remove trailing publisher text like "(AssociationforComputingMachinery...)"
                # This handles nested parentheses like "(JohnWiley&SonsLtd(2016))"
                # Remove everything from first "(" followed by a letter to the end
                doi = re.sub(r"\([A-Za-z].*$", "", doi)

                # Remove trailing URLs/domains that got attached (page headers/footers)
                # Pattern: ".www.domain.com..." or ".nature.com..." etc
                doi = re.sub(
                    r"\.(?:www\.)?[a-z]+\.[a-z]+(?:\.[a-z]+)?/.*$",
                    "",
                    doi,
                    flags=re.IGNORECASE,
                )

                # Remove text after DOI when it continues into next reference or article title
                # Patterns that indicate we've gone past the DOI:
                # 1. ".PrinciplesofNeuralScience" - period + capitalized title
                # 2. ".T.-S.Dalsgaard" - period + author name pattern (including initials)
                # 3. ".In:" - period + common continuation word
                # Strategy: Remove period + capital letter + anything after it
                # BUT: Don't match if followed immediately by a digit (part of DOI like ".A123")
                doi = re.sub(r"\.([A-Z][^0-9/]).*$", "", doi)
                # Re-add the period if we removed it (was part of ending punctuation, not continuation)
                if doi and not doi.endswith((".", "/")):
                    # Check if original had more content - if last char is letter, don't add period
                    pass

                # Clean up any trailing punctuation that's not part of DOI
                doi = re.sub(r"[,;.\s]+$", "", doi)

                # Remove trailing periods and other punctuation
                doi = doi.rstrip(".,;:/")

                return doi

        return None

    def _extract_title_from_reference(self, ref_text: str) -> Optional[str]:
        """
        Extract title from a reference text with improved heuristics

        Args:
            ref_text: Raw reference text (normalized to single line)

        Returns:
            Extracted title or None
        """
        # Try to extract title in quotes first (most reliable)
        quote_patterns = [
            r'"([^"]+)"',  # Double quotes
            r"'([^']+)'",  # Single quotes
            r'"([^"]+)"',  # Smart quotes
            r"'([^']+)'",  # Smart single quotes
        ]

        for pattern in quote_patterns:
            match = re.search(pattern, ref_text)
            if match:
                title = match.group(1).strip()
                if len(title) > 10:
                    return title

        # EDITED BOOK PATTERN: "Authors (Eds.), Title. Publisher..."
        # Example: "Wiertlewski, M., Smeets, J. (Eds.), Haptics: Science, Technology, Applications. Springer..."
        edited_book_match = re.search(
            r"\(Eds?\.\),\s+([^.]+?)\.", ref_text, re.IGNORECASE
        )
        if edited_book_match:
            title = edited_book_match.group(1).strip()
            if len(title) > 10:
                return title

        # AUTHOR-YEAR FORMAT: Title after year with distinctive punctuation
        # Handles titles ending with colon, question mark, or exclamation
        # Example: "Sharpe, D., 2019. Chi-square test is statistically significant: now what? Pract..."
        # This pattern captures title that ends with punctuation before an abbreviated word
        year_title_match = re.search(
            r"\b\d{4}\.\s+([^.]+[:.?!])\s+(?:[A-Z][a-z]*\.|\b(?:In|Proceedings|Journal))",
            ref_text,
        )
        if year_title_match:
            title = year_title_match.group(1).strip()
            # Remove trailing punctuation if it's just the marker
            title = re.sub(r"\s*[:.?!]\s*$", "", title)
            if len(title) > 10:
                return title

        # DATASET/REPORT PATTERN: "Authors, Year. Title -. dataset/report."
        # Example: "Dalsgaard, T.-S., ..., 2022. A user-derived mapping for mid-air haptic experiences -. dataset."
        dataset_match = re.search(
            r"\b\d{4}\.\s+([^.]+?)\s*-\.\s*(?:dataset|report)", ref_text, re.IGNORECASE
        )
        if dataset_match:
            title = dataset_match.group(1).strip()
            if len(title) > 10:
                return title

        # BOOK PATTERN: Title (Publisher, Location, Year), edition
        # Examples:
        # - "Chemesthesis: Chemical Touch in Food and Eating (John Wiley & Sons, Inc, Chichester, West Sussex, 2016), 1. edn."
        # - "Principles of Neural Science (McGraw-Hill, New York, 2021), 6th edn."
        book_match = re.search(
            r"([A-Z][^.(]+?)\s*\(([^)]+,\s+[^)]+,\s+\d{4})\)", ref_text
        )
        if book_match:
            title = book_match.group(1).strip()
            # Clean up trailing connectors and editor notes
            title = re.sub(
                r"\s+(eds?\.|ed\.|editors?|edited by)$", "", title, flags=re.IGNORECASE
            )
            if len(title) > 10 and not self._looks_like_authors(title):
                return title

        # BOOK CHAPTER PATTERN: "Authors. ChapterTitle. BookTitle pages (Year)."
        # Example: "Sawka, M. N., ... Physiological responses to exercise in the heat. Nutritional needs in hot environments: applications for military personnel in field operations 55 (1993)."
        # Pattern: Two sentences before "NUMBER (YEAR)"
        book_chapter_match = re.search(
            r"\.\s+([A-Z][^.]+)\.\s+([A-Z][^.]+?)\s+\d+\s+\(\d{4}\)", ref_text
        )
        if book_chapter_match:
            title1 = book_chapter_match.group(1).strip()
            title2 = book_chapter_match.group(2).strip()

            # Chapter title is usually shorter and doesn't have colons; book title often has colons
            if (
                ":" not in title1
                and len(title1) > 20
                and not self._looks_like_authors(title1)
            ):
                return title1

        # JOURNAL ARTICLE PATTERN 1: "Authors. Title. Journal Volume, Pages (Year)."
        # Examples:
        # - "Hirayama, R., ... S. A volumetric display for visual, tactile and audio presentation using acoustic trapping. Nature 575, 320–323 (2019)."
        # - "Wood, S. N. Fast stable restricted maximum likelihood... Journal of the Royal Statistical Society (B) 73, 3–36 (2011)."
        # Pattern: Sentence ending with "JournalName Number, Number-Number (Year)"
        journal_article_match = re.search(
            r"([A-Z][^.]+)\.\s+([A-Z][^.]+?)\s+\d+,\s+\d+[–-]\d+\s+\(\d{4}\)", ref_text
        )
        if journal_article_match:
            potential_title = journal_article_match.group(1).strip()
            journal_name = journal_article_match.group(2).strip()

            # Check if potential_title doesn't look like authors and journal_name looks like a journal
            if (
                len(potential_title) > 20
                and not self._looks_like_authors(potential_title)
                and len(journal_name.split()) <= 8
            ):  # Journal names are usually short
                return potential_title

        # JOURNAL ARTICLE PATTERN 2: Handle "Authors. Title. Journal, volume:pages, year." pattern
        # Pattern: Text ends with journal-like string followed by volume/pages and year
        # Example: "M. Hassenzahl. Engineering joy. IEEE Software, 18(1):70–76, 2001."
        journal_pattern = r"^([^.]+\.)\s+([^.]+)\.\s+((?:IEEE|ACM|Proc\.|Proceedings|Journal|International|Conference|In\s+[A-Z]|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})[^.]*,?\s+\d+.*\d{4}[.,]?\s*$)"
        journal_match = re.match(journal_pattern, ref_text, re.IGNORECASE)
        if journal_match:
            potential_title = journal_match.group(2).strip()
            # Verify it's not author names and has reasonable length
            if len(potential_title) > 10 and not self._looks_like_authors(
                potential_title
            ):
                # Extra check: shouldn't end with year (that would be part 1, not title)
                if not re.search(r"\b(19|20)\d{2}$", potential_title):
                    return potential_title

        # Common citation formats:
        # 1. Authors. Year. Title. Journal/Conference.
        # 2. Authors (Year). Title. Journal/Conference.
        # 3. Authors. Title. Journal Year.
        # 4. Authors. Title. Journal, volume:pages, year. (handled above)

        # Try to find year position
        year_match = re.search(r"\b(19|20)\d{2}\b", ref_text)
        if not year_match:
            return None

        year_pos = year_match.start()
        year_val = year_match.group(0)

        # Split reference into parts using periods as delimiters
        # but keep track of positions
        # IMPORTANT: Don't split on periods that are part of initials (e.g., "A. Jorge")
        parts = []
        current_pos = 0

        # More intelligent period detection: skip periods in initials
        # Pattern: period not preceded by a single capital letter (initial)
        # We want to split on: ". " where the char before . is NOT: "single capital letter"
        for match in re.finditer(r"\.(?:\s+|$)", ref_text):
            period_pos = match.start()

            # Check if this is an initial: single capital letter before period
            # Look at the character(s) before the period
            if period_pos > 0:
                # Check the word before the period
                # If it's a single capital letter (possibly preceded by space), it's an initial
                before_period = ref_text[max(0, period_pos - 3) : period_pos]

                # Skip if it looks like an initial: " A." or ", A." or "M. A."
                if re.search(r"(?:^|[\s,])([A-Z])$", before_period):
                    continue

            part = ref_text[current_pos : match.start()].strip()
            if part:
                parts.append((part, current_pos, match.start()))
            current_pos = match.end()

        # Add remaining text if any
        if current_pos < len(ref_text):
            part = ref_text[current_pos:].strip()
            if part:
                parts.append((part, current_pos, len(ref_text)))

        if len(parts) < 2:
            return None

        # Find which part contains the year
        year_part_idx = None
        for idx, (part, start, end) in enumerate(parts):
            if start <= year_pos < end:
                year_part_idx = idx
                break

        if year_part_idx is None:
            return None

        # Strategy 1: If year is in first part (e.g., "Authors 2020"), title is likely second part
        if year_part_idx == 0:
            if len(parts) > 1:
                title = parts[1][0]
                # Remove common prefixes
                title = re.sub(
                    r"^(In |Proceedings of |Conference on )",
                    "",
                    title,
                    flags=re.IGNORECASE,
                )
                if len(title) > 15 and not self._looks_like_authors(title):
                    return title

        # Strategy 2: If year is in second part or later, title is likely the part before year
        # unless the first part is very long (likely contains title)
        elif year_part_idx > 0:
            # Check if first part is just authors (short, has "and", has initials)
            first_part = parts[0][0]
            if self._looks_like_authors(first_part) and len(parts) > 1:
                # Title is likely second part (before or after year)
                if year_part_idx == 1:
                    # Year in second part: could be "Authors. 2020 Title. Conference" or "Authors. 2020. Title. Conference"
                    year_part_text = parts[1][0]

                    # Check if year is alone or has text after it
                    if year_part_text.strip() == year_val:
                        # Year is alone in this part, title is likely next part
                        if len(parts) > 2:
                            title = parts[2][0]
                            # Clean up common prefixes
                            title = re.sub(
                                r"^(In |Proceedings of |Conference on )",
                                "",
                                title,
                                flags=re.IGNORECASE,
                            )
                            if len(title) > 15 and not self._looks_like_authors(title):
                                return title
                    else:
                        # Year has text after it in same part: "Authors. 2020 Title. Conference"
                        # Extract text after year in same part
                        year_end = year_pos - parts[1][1] + 4  # Position within part
                        title_text = parts[1][0][year_end:].strip()
                        title_text = re.sub(r"^[.,;\s]+", "", title_text)
                        if len(title_text) > 15:
                            # Take until next sentence indicator
                            title_match = re.match(r"^([^.]+)", title_text)
                            if title_match:
                                return title_match.group(1).strip()
                else:
                    # Year in later part, title is second part
                    title = parts[1][0]
                    if len(title) > 15 and not self._looks_like_authors(title):
                        return title

        # Fallback: look for capitalized title-like text between author names and venue
        # Pattern: look for text that starts with capital letter and contains multiple words
        for part, start, end in parts[1:]:  # Skip first part (likely authors)
            if len(part) > 20 and re.match(r"^[A-Z]", part):
                # Check if it's not a venue/journal (usually has keywords like "Proceedings", "Conference", "Journal")
                if not re.search(
                    r"(?:Proceedings|Conference|Journal|Symposium|Workshop|ACM|IEEE)\b",
                    part,
                    re.IGNORECASE,
                ):
                    return part

        return None

    def _looks_like_authors(self, text: str) -> bool:
        """
        Check if text looks like author names

        Args:
            text: Text to check

        Returns:
            True if text likely contains author names
        """
        # Author indicators:
        # - Contains "and" (connecting authors)
        # - Contains initials (capital letters followed by period)
        # - Contains comma-separated names
        # - Relatively short (< 150 chars typically)

        if len(text) > 200:
            return False

        indicators = 0

        if re.search(r"\band\b", text, re.IGNORECASE):
            indicators += 1
        if re.search(r"\b[A-Z]\.\s*[A-Z]?\.?", text):  # Initials like "J. M." or "J."
            indicators += 1
        if text.count(",") >= 2:  # Multiple commas for author list
            indicators += 1
        if re.search(r"\bet\s+al\.?\b", text, re.IGNORECASE):  # "et al."
            indicators += 2

        return indicators >= 2

    def _extract_first_author_surname(self, ref_text: str) -> Optional[str]:
        """
        Extract first author's surname from reference text

        Args:
            ref_text: Raw reference text

        Returns:
            First author surname or None
        """
        # Pattern: "Surname, Initial" or "Initial. Surname" at start
        # Examples: "M. Hassenzahl", "Hassenzahl, M.", "Hassenzahl"

        # Try "Surname, Initial" format first
        match = re.match(r"^([A-Z][a-z]+(?:-[A-Z][a-z]+)?),\s*[A-Z]", ref_text)
        if match:
            return match.group(1)

        # Try "Initial. Surname" or just "Surname"
        match = re.match(r"^(?:[A-Z]\.\s+)?([A-Z][a-z]+(?:-[A-Z][a-z]+)?)", ref_text)
        if match:
            return match.group(1)

        return None

    def _extract_year_from_reference(self, ref_text: str) -> Optional[int]:
        """
        Extract publication year from reference text

        Args:
            ref_text: Raw reference text

        Returns:
            Publication year or None
        """
        # Look for 4-digit year (19xx or 20xx)
        matches = re.findall(r"\b(19\d{2}|20\d{2})\b", ref_text)
        if matches:
            return int(matches[0])
        return None

    def extract_references(self) -> List[Dict[str, Optional[str]]]:
        """
        Extract all references from the PDF

        Returns:
            List of dictionaries containing reference information (doi, title, year, raw_text)
        """
        text = self.extract_text()
        refs_section = self.find_references_section(text)

        if refs_section:
            print(f"✓ Found references section ({len(refs_section)} characters)")
            references = self.parse_individual_references(refs_section)
        else:
            print(
                "⚠ Warning: Could not identify references section, searching entire document for DOIs"
            )
            # Fallback: just extract DOIs
            dois = self.extract_dois_from_text(text)
            references = [
                {"raw_text": doi, "doi": doi, "title": None, "year": None}
                for doi in dois
            ]

        return references
