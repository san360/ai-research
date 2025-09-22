"""
Unit tests for citation utilities.

Tests for single, duplicate, out-of-order, and consecutive superscripts;
verification of consolidation and sorting functionality.
"""

import pytest
from deep_research_ui.utils.citations import (
    convert_citations_to_superscript,
    extract_citations_from_annotations,
    format_citations_for_display
)


class TestConvertCitationsToSuperscript:
    """Test cases for citation conversion to superscript format."""
    
    def test_single_citation(self):
        """Test conversion of a single citation marker."""
        input_text = "This is a test 【1:3†source】 with one citation."
        expected = "This is a test <sup>3</sup> with one citation."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_multiple_separate_citations(self):
        """Test conversion of multiple separate citation markers."""
        input_text = "First 【1:3†source】 and second 【2:7†source】 citations."
        expected = "First <sup>3</sup> and second <sup>7</sup> citations."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_consecutive_citations_consolidation(self):
        """Test consolidation of consecutive citation markers."""
        input_text = "Text 【1:5†source】【2:3†source】【3:8†source】 here."
        expected = "Text <sup>3,5,8</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_consecutive_citations_with_commas(self):
        """Test consolidation when citations already have commas."""
        input_text = "Text 【1:5†source】, 【2:3†source】, 【3:8†source】 here."
        expected = "Text <sup>3,5,8</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_duplicate_citations_removal(self):
        """Test removal of duplicate citation numbers."""
        input_text = "Text 【1:5†source】【2:3†source】【3:5†source】 here."
        expected = "Text <sup>3,5</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_out_of_order_citations_sorting(self):
        """Test sorting of out-of-order citation numbers."""
        input_text = "Text 【1:9†source】【2:2†source】【3:6†source】 here."
        expected = "Text <sup>2,6,9</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_mixed_consecutive_and_separate(self):
        """Test mix of consecutive and separate citations."""
        input_text = "First 【1:3†source】【2:7†source】 and later 【3:1†source】 text."
        expected = "First <sup>3,7</sup> and later <sup>1</sup> text."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_no_citations(self):
        """Test text with no citation markers."""
        input_text = "This text has no citations."
        expected = "This text has no citations."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_empty_string(self):
        """Test empty string input."""
        result = convert_citations_to_superscript("")
        assert result == ""
    
    def test_single_consecutive_citation(self):
        """Test single citation that would match consecutive pattern."""
        input_text = "Text 【1:5†source】 here."
        expected = "Text <sup>5</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected
    
    def test_large_citation_numbers(self):
        """Test with large citation numbers."""
        input_text = "Text 【99:123†source】【100:456†source】 here."
        expected = "Text <sup>123,456</sup> here."
        result = convert_citations_to_superscript(input_text)
        assert result == expected


class MockAnnotation:
    """Mock citation annotation for testing."""
    
    def __init__(self, url: str, title: str = None):
        self.url_citation = MockUrlCitation(url, title)
        self.text = f"annotation_for_{url}"


class MockUrlCitation:
    """Mock URL citation for testing."""
    
    def __init__(self, url: str, title: str = None):
        self.url = url
        self.title = title


class TestExtractCitationsFromAnnotations:
    """Test cases for extracting citations from annotations."""
    
    def test_extract_single_citation(self):
        """Test extracting a single citation."""
        annotations = [MockAnnotation("http://example.com", "Example Title")]
        result = extract_citations_from_annotations(annotations)
        expected = {"http://example.com": "Example Title"}
        assert result == expected
    
    def test_extract_multiple_citations(self):
        """Test extracting multiple citations."""
        annotations = [
            MockAnnotation("http://example1.com", "Title 1"),
            MockAnnotation("http://example2.com", "Title 2"),
        ]
        result = extract_citations_from_annotations(annotations)
        expected = {
            "http://example1.com": "Title 1",
            "http://example2.com": "Title 2"
        }
        assert result == expected
    
    def test_extract_citation_no_title(self):
        """Test extracting citation without title (uses URL as title)."""
        annotations = [MockAnnotation("http://example.com")]
        result = extract_citations_from_annotations(annotations)
        expected = {"http://example.com": "http://example.com"}
        assert result == expected
    
    def test_extract_empty_annotations(self):
        """Test extracting from empty annotations list."""
        result = extract_citations_from_annotations([])
        assert result == {}


class TestFormatCitationsForDisplay:
    """Test cases for formatting citations for UI display."""
    
    def test_format_single_citation(self):
        """Test formatting a single citation."""
        citations = {"http://example.com": "Example Title"}
        result = format_citations_for_display(citations)
        expected = "1. [Example Title](http://example.com)"
        assert result == expected
    
    def test_format_multiple_citations(self):
        """Test formatting multiple citations."""
        citations = {
            "http://example1.com": "Title 1",
            "http://example2.com": "Title 2"
        }
        result = format_citations_for_display(citations)
        # Note: dict order might vary, so check each line
        lines = result.split("\n")
        assert len(lines) == 2
        assert all(line.startswith(("1. ", "2. ")) for line in lines)
        assert "[Title 1](http://example1.com)" in result
        assert "[Title 2](http://example2.com)" in result
    
    def test_format_empty_citations(self):
        """Test formatting empty citations dictionary."""
        result = format_citations_for_display({})
        assert result == "No citations found."
    
    def test_format_citation_url_as_title(self):
        """Test formatting citation where URL is used as title."""
        citations = {"http://example.com": "http://example.com"}
        result = format_citations_for_display(citations)
        expected = "1. [http://example.com](http://example.com)"
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__])