"""
Telemetry and tracing configuration for Azure Agents Deep Research.

This module provides utilities for configuring OpenTelemetry tracing and Azure Monitor
integration for comprehensive observability of the research process.
"""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from azure.ai.agents.telemetry import AIAgentsInstrumentor


def configure_telemetry(project_client: AIProjectClient) -> None:
    """
    Configure Azure Monitor telemetry and OpenTelemetry tracing.
    
    Args:
        project_client (AIProjectClient): Azure AI Project client for getting connection string
    """
    # Enable tracing for AI content (optional - contains message content)
    os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
    
    # Get Application Insights connection string and configure Azure Monitor
    connection_string = project_client.telemetry.get_application_insights_connection_string()
    configure_azure_monitor(connection_string=connection_string)
    
    # Instrument AI Agents for tracing
    AIAgentsInstrumentor().instrument()


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get an OpenTelemetry tracer instance.
    
    Args:
        name (str): Name for the tracer, defaults to current module
        
    Returns:
        trace.Tracer: Configured tracer instance
    """
    return trace.get_tracer(name)


@contextmanager
def trace_operation(operation_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for tracing operations with automatic span management.
    
    Args:
        operation_name (str): Name of the operation being traced
        attributes (Optional[Dict[str, Any]]): Optional attributes to set on the span
        
    Yields:
        Span: The created span for setting additional attributes
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span(operation_name) as span:
        # Set initial attributes if provided
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
        except Exception as e:
            # Record exception in span
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise


def add_research_span_attributes(
    span: trace.Span,
    agent_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    run_id: Optional[str] = None,
    query: Optional[str] = None,
    iteration_count: Optional[int] = None
) -> None:
    """
    Add common research-related attributes to a span.
    
    Args:
        span (trace.Span): The span to add attributes to
        agent_id (Optional[str]): Agent ID if available
        thread_id (Optional[str]): Thread ID if available
        run_id (Optional[str]): Run ID if available
        query (Optional[str]): Research query if available
        iteration_count (Optional[int]): Current iteration count if available
    """
    if agent_id:
        span.set_attribute("agent.id", agent_id)
    if thread_id:
        span.set_attribute("thread.id", thread_id)
    if run_id:
        span.set_attribute("run.id", run_id)
    if query:
        span.set_attribute("research.query", query)
        span.set_attribute("research.query_length", len(query))
    if iteration_count is not None:
        span.set_attribute("research.iteration_count", iteration_count)


def add_message_span_attributes(
    span: trace.Span,
    message_id: Optional[str] = None,
    content_length: Optional[int] = None,
    citations_count: Optional[int] = None,
    is_new_content: Optional[bool] = None
) -> None:
    """
    Add message-related attributes to a span.
    
    Args:
        span (trace.Span): The span to add attributes to
        message_id (Optional[str]): Message ID if available
        content_length (Optional[int]): Length of message content if available
        citations_count (Optional[int]): Number of citations if available
        is_new_content (Optional[bool]): Whether this is new content if known
    """
    if message_id:
        span.set_attribute("message.id", message_id)
    if content_length is not None:
        span.set_attribute("message.content_length", content_length)
    if citations_count is not None:
        span.set_attribute("message.citations_count", citations_count)
    if is_new_content is not None:
        span.set_attribute("message.is_new_content", is_new_content)