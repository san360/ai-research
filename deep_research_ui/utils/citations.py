"""
Citation utilities for converting Deep Research citation markers to HTML superscript format.

This module provides functionality to convert citation patterns from Azure Agents Deep Research
results into properly formatted HTML superscript citations with consolidation and sorting.
"""

import re
from typing import List, Dict
from opentelemetry import trace


def convert_citations_to_superscript(markdown_content: str) -> str:
    """
    Convert citation markers in markdown content to HTML superscript format.

    This function finds citation patterns like 【78:12†source】 and converts them to
    HTML superscript tags <sup>12</sup> for better formatting in markdown documents.
    It also consolidates consecutive citations by sorting and deduplicating them.

    Args:
        markdown_content (str): The markdown content containing citation markers

    Returns:
        str: The markdown content with citations converted to HTML superscript format
    """
    # Get tracer for this function
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("convert_citations_to_superscript") as span:
        span.set_attribute("input.content_length", len(markdown_content))
        
        # Pattern to match 【number:number†source】or similar citation markers
        # This pattern is more flexible to handle different citation types
        pattern = r"\u3010\d+:(\d+)\u2020\w+\u3011"

        # Replace with <sup>captured_number</sup>
        def replacement(match):
            citation_number = match.group(1)
            return f"<sup>{citation_number}</sup>"

        # First, convert all citation markers to superscript
        converted_text = re.sub(pattern, replacement, markdown_content)
        
        # Count initial citations
        initial_citations = len(re.findall(pattern, markdown_content))
        span.set_attribute("citations.initial_count", initial_citations)

        # Then, consolidate consecutive superscript citations
        # Pattern to match multiple superscript tags with optional commas/spaces
        # Matches: <sup>5</sup>,<sup>4</sup>,<sup>5</sup> or <sup>5</sup><sup>4</sup><sup>5</sup>
        consecutive_pattern = r"(<sup>\d+</sup>)(\s*,?\s*<sup>\d+</sup>)+"

        def consolidate_and_sort_citations(match):
            # Extract all citation numbers from the matched text
            citation_text = match.group(0)
            citation_numbers = re.findall(r"<sup>(\d+)</sup>", citation_text)

            # Convert to integers, remove duplicates, and sort
            unique_sorted_citations = sorted(set(int(num) for num in citation_numbers))

            # If only one citation, return simple format
            if len(unique_sorted_citations) == 1:
                return f"<sup>{unique_sorted_citations[0]}</sup>"

            # If multiple citations, return comma-separated format
            citation_list = ",".join(str(num) for num in unique_sorted_citations)
            return f"<sup>{citation_list}</sup>"

        # Remove consecutive duplicate citations and sort them
        final_text = re.sub(consecutive_pattern, consolidate_and_sort_citations, converted_text)
        
        # Count final superscript citations
        final_citations = len(re.findall(r"<sup>[^<>]+</sup>", final_text))
        span.set_attribute("citations.final_count", final_citations)
        span.set_attribute("output.content_length", len(final_text))

        return final_text


def extract_citations_from_annotations(annotations: List) -> Dict[str, str]:
    """
    Extract unique citations from URL citation annotations.

    Args:
        annotations (List): List of URL citation annotations from agent response

    Returns:
        Dict[str, str]: Dictionary mapping URLs to titles
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("extract_citations") as span:
        citations = {}
        
        for ann in annotations:
            url = ann.url_citation.url
            title = ann.url_citation.title or url
            citations[url] = title
        
        span.set_attribute("citations.extracted_count", len(citations))
        return citations


def format_citations_for_display(citations: Dict[str, str]) -> str:
    """
    Format citations dictionary into markdown list for UI display.

    Args:
        citations (Dict[str, str]): Dictionary mapping URLs to titles

    Returns:
        str: Formatted markdown string with numbered citations
    """
    if not citations:
        return "No citations found."
    
    formatted_citations = []
    for i, (url, title) in enumerate(citations.items(), 1):
        formatted_citations.append(f"{i}. [{title}]({url})")
    
    return "\n".join(formatted_citations)