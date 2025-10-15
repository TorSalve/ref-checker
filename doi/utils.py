"""
Utility functions for data cleaning and text processing
"""

from typing import Optional, Any, List, Dict


def clean_text_for_csv(text: Optional[str]) -> Optional[str]:
    """
    Clean text for CSV export by removing/replacing problematic characters

    Args:
        text: Input text string

    Returns:
        Cleaned text suitable for CSV
    """
    if text is None:
        return None

    # Replace newlines and carriage returns with spaces
    text = text.replace("\n", " ").replace("\r", " ")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Collapse multiple spaces into single space
    import re

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_text_for_json(text: Optional[str]) -> Optional[str]:
    """
    Clean text for JSON export by normalizing whitespace

    Args:
        text: Input text string

    Returns:
        Cleaned text suitable for JSON
    """
    if text is None:
        return None

    import re

    # Replace multiple newlines with double newline (preserve paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into single space (but preserve newlines)
    lines = text.split("\n")
    cleaned_lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in lines]
    text = "\n".join(cleaned_lines)

    return text.strip()


def clean_data_structure(data: Any, for_csv: bool = False) -> Any:
    """
    Recursively clean a data structure (dict, list, or string)

    Args:
        data: Data to clean (dict, list, str, or other)
        for_csv: If True, use CSV cleaning; otherwise use JSON cleaning

    Returns:
        Cleaned data structure
    """
    if isinstance(data, dict):
        return {
            key: clean_data_structure(value, for_csv) for key, value in data.items()
        }
    elif isinstance(data, list):
        return [clean_data_structure(item, for_csv) for item in data]
    elif isinstance(data, str):
        if for_csv:
            return clean_text_for_csv(data)
        else:
            return clean_text_for_json(data)
    else:
        return data
