"""
Research report builder for generating formatted reports with citations.

This module handles the creation of research summaries with proper markdown formatting,
superscript conversion, and optional file output.
"""

import os
import sys
from typing import Tuple, List, Dict, Optional
from azure.ai.agents.models import ThreadMessage

# Add parent directory to path to support imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from deep_research_ui.utils.citations import convert_citations_to_superscript, extract_citations_from_annotations
    from deep_research_ui.telemetry.tracing import trace_operation
except ImportError:
    # Fallback to relative imports
    from ..utils.citations import convert_citations_to_superscript, extract_citations_from_annotations
    from ..telemetry.tracing import trace_operation


def create_research_summary(
    message: ThreadMessage,
    save_to_file: bool = True,
    filepath: str = "research_report.md"
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Create a formatted research report from an agent's thread message with numbered citations.
    
    Args:
        message (ThreadMessage): The thread message containing the agent's research response
        save_to_file (bool): Whether to save the report to a file
        filepath (str): Path where the research summary will be saved if save_to_file is True
        
    Returns:
        Tuple[str, List[Dict[str, str]]]: (markdown_content, citations_list)
            - markdown_content: The formatted markdown report with superscript citations
            - citations_list: List of dicts with 'title' and 'url' keys
    """
    with trace_operation("create_research_summary", {
        "output.filepath": filepath if save_to_file else "none",
        "save_to_file": save_to_file
    }) as span:
        
        if not message:
            span.set_attribute("summary.created", False)
            span.set_attribute("error", "No message content provided")
            return "No message content provided.", []
        
        span.set_attribute("message.has_text", len(message.text_messages) > 0)
        span.set_attribute("message.text_messages_count", len(message.text_messages))
        span.set_attribute("message.citations_count", len(message.url_citation_annotations))
        
        # Build text summary
        text_summary = "\n\n".join([t.text.value.strip() for t in message.text_messages])
        
        # Convert citations to superscript format
        formatted_text = convert_citations_to_superscript(text_summary)
        
        # Extract unique citations
        citations_dict = extract_citations_from_annotations(message.url_citation_annotations)
        citations_list = [{"title": title, "url": url} for url, title in citations_dict.items()]
        
        # Build complete markdown report
        markdown_content = formatted_text
        
        if citations_list:
            markdown_content += "\n\n## Citations\n"
            for i, citation in enumerate(citations_list, 1):
                markdown_content += f"{i}. [{citation['title']}]({citation['url']})\n"
        
        span.set_attribute("summary.unique_citations_count", len(citations_list))
        span.set_attribute("summary.content_length", len(markdown_content))
        
        # Save to file if requested
        if save_to_file:
            _save_report_to_file(markdown_content, filepath, span)
        
        span.set_attribute("summary.created", True)
        return markdown_content, citations_list


def _save_report_to_file(content: str, filepath: str, span) -> None:
    """
    Save report content to a file.
    
    Args:
        content (str): The markdown content to save
        filepath (str): Path to save the file
        span: The tracing span to add attributes to
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as fp:
            fp.write(content)
        
        span.set_attribute("summary.file_saved", True)
        span.set_attribute("summary.file_size_bytes", os.path.getsize(filepath))
        
    except Exception as e:
        span.set_attribute("summary.file_saved", False)
        span.set_attribute("summary.file_error", str(e))
        raise


def format_citations_for_ui(citations_dict: Dict[str, str]) -> str:
    """
    Format citations dictionary into markdown list for UI display.
    
    Args:
        citations_dict (Dict[str, str]): Dictionary mapping URLs to titles
        
    Returns:
        str: Formatted markdown string with numbered citations
    """
    if not citations_dict:
        return "No citations found yet..."
    
    formatted_citations = []
    for i, (url, title) in enumerate(citations_dict.items(), 1):
        formatted_citations.append(f"{i}. [{title}]({url})")
    
    return "\n".join(formatted_citations)


def create_progress_file_content(ui_buffer: List[str]) -> str:
    """
    Create content for the progress file from UI buffer.
    
    Args:
        ui_buffer (List[str]): List of progress lines from UI
        
    Returns:
        str: Formatted content for progress file
    """
    if not ui_buffer:
        return "No progress recorded."
    
    return "\n".join(ui_buffer)


def get_research_metrics(
    final_message: Optional[ThreadMessage],
    citations_count: int,
    elapsed_time: float,
    iteration_count: int
) -> Dict[str, any]:
    """
    Generate summary metrics for the research session.
    
    Args:
        final_message (Optional[ThreadMessage]): Final agent message
        citations_count (int): Total number of unique citations
        elapsed_time (float): Total elapsed time in seconds
        iteration_count (int): Number of polling iterations
        
    Returns:
        Dict[str, any]: Dictionary of metrics
    """
    metrics = {
        "total_citations": citations_count,
        "elapsed_time_seconds": elapsed_time,
        "elapsed_time_formatted": f"{elapsed_time:.1f}s",
        "iteration_count": iteration_count,
        "average_iteration_time": elapsed_time / max(iteration_count, 1),
        "has_final_message": final_message is not None,
    }
    
    if final_message:
        metrics.update({
            "final_message_length": sum(len(t.text.value) for t in final_message.text_messages),
            "final_message_citations": len(final_message.url_citation_annotations),
        })
    
    return metrics