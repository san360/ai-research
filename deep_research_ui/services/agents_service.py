"""
Azure Agents service for Deep Research operations.

This module wraps all Azure Agents interactions including client creation, agent management,
run execution, and polling with live progress updates through configurable sinks.
"""

import os
import sys
import time
from typing import Optional, Tuple, Callable, Dict, Any
from azure.ai.projects import AIProjectClient
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import DeepResearchTool, MessageRole, ThreadMessage, Agent, AgentThread, ThreadRun
from azure.identity import DefaultAzureCredential

# Add parent directory to path to support imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from deep_research_ui.utils.logging_sinks import ProgressSink
    from deep_research_ui.utils.citations import extract_citations_from_annotations
    from deep_research_ui.telemetry.tracing import configure_telemetry, trace_operation, add_research_span_attributes, add_message_span_attributes
except ImportError:
    # Fallback to relative imports
    from ..utils.logging_sinks import ProgressSink
    from ..utils.citations import extract_citations_from_annotations
    from ..telemetry.tracing import configure_telemetry, trace_operation, add_research_span_attributes, add_message_span_attributes


class AgentsService:
    """Service for managing Azure Agents Deep Research operations."""
    
    def __init__(self):
        """Initialize the agents service."""
        self.project_client: Optional[AIProjectClient] = None
        self.agents_client: Optional[AgentsClient] = None
    
    def create_clients(
        self,
        endpoint: str,
        credential: Optional[DefaultAzureCredential] = None
    ) -> Tuple[AIProjectClient, AgentsClient]:
        """
        Create and configure Azure AI Project and Agents clients.
        
        Args:
            endpoint (str): Azure AI Project endpoint
            credential (Optional[DefaultAzureCredential]): Azure credential, creates new if None
            
        Returns:
            Tuple[AIProjectClient, AgentsClient]: Configured client instances
        """
        if credential is None:
            credential = DefaultAzureCredential()
        
        self.project_client = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )
        
        # Configure telemetry and tracing
        configure_telemetry(self.project_client)
        
        self.agents_client = self.project_client.agents
        
        return self.project_client, self.agents_client
    
    def create_agent(
        self,
        model_deployment_name: str,
        deep_research_model_deployment_name: str,
        bing_resource_name: str,
        agent_name: str = "research-agent",
        instructions: str = "You are a helpful Agent that assists in researching scientific topics."
    ) -> Agent:
        """
        Create an agent with Deep Research tool configured.
        
        Args:
            model_deployment_name (str): Arbitration model deployment name
            deep_research_model_deployment_name (str): Deep Research model deployment name
            bing_resource_name (str): Bing Search resource name
            agent_name (str): Name for the agent
            instructions (str): Instructions for the agent
            
        Returns:
            Agent: Created agent instance
        """
        if not self.project_client or not self.agents_client:
            raise ValueError("Clients not initialized. Call create_clients() first.")
        
        with trace_operation("create_agent", {
            "agent.name": agent_name,
            "agent.model": model_deployment_name,
            "deep_research.model": deep_research_model_deployment_name
        }) as span:
            # Get Bing connection
            bing_connection = self.project_client.connections.get(name=bing_resource_name)
            span.set_attribute("bing.connection_id", bing_connection.id)
            
            # Initialize Deep Research tool
            deep_research_tool = DeepResearchTool(
                bing_grounding_connection_id=bing_connection.id,
                deep_research_model=deep_research_model_deployment_name,
            )
            
            # Create agent
            agent = self.agents_client.create_agent(
                model=model_deployment_name,
                name=agent_name,
                instructions=instructions,
                tools=deep_research_tool.definitions,
            )
            
            span.set_attribute("agent.id", agent.id)
            return agent
    
    def create_thread(self) -> AgentThread:
        """
        Create a new thread for communication.
        
        Returns:
            AgentThread: Created thread instance
        """
        if not self.agents_client:
            raise ValueError("Agents client not initialized. Call create_clients() first.")
        
        with trace_operation("create_thread") as span:
            thread = self.agents_client.threads.create()
            span.set_attribute("thread.id", thread.id)
            return thread
    
    def create_message(self, thread_id: str, content: str, role: str = "user") -> ThreadMessage:
        """
        Create a message in a thread.
        
        Args:
            thread_id (str): ID of the thread
            content (str): Message content
            role (str): Message role (default: "user")
            
        Returns:
            ThreadMessage: Created message
        """
        if not self.agents_client:
            raise ValueError("Agents client not initialized. Call create_clients() first.")
        
        with trace_operation("create_message", {
            "thread.id": thread_id,
            "message.role": role,
            "message.content_length": len(content)
        }) as span:
            message = self.agents_client.messages.create(
                thread_id=thread_id,
                role=role,
                content=content,
            )
            span.set_attribute("message.id", message.id)
            return message
    
    def start_run(self, thread_id: str, agent_id: str) -> ThreadRun:
        """
        Start a run for the given thread and agent.
        
        Args:
            thread_id (str): ID of the thread
            agent_id (str): ID of the agent
            
        Returns:
            ThreadRun: Started run instance
        """
        if not self.agents_client:
            raise ValueError("Agents client not initialized. Call create_clients() first.")
        
        with trace_operation("start_run", {
            "thread.id": thread_id,
            "agent.id": agent_id
        }) as span:
            run = self.agents_client.runs.create(thread_id=thread_id, agent_id=agent_id)
            span.set_attribute("run.id", run.id)
            span.set_attribute("run.initial_status", run.status)
            return run
    
    def poll_run(
        self,
        thread_id: str,
        run_id: str,
        sinks: ProgressSink,
        on_citation: Optional[Callable[[str, str], None]] = None,
        poll_interval: float = 1.0
    ) -> Tuple[str, Optional[ThreadMessage]]:
        """
        Poll a run until completion, streaming progress through sinks.
        
        Args:
            thread_id (str): ID of the thread
            run_id (str): ID of the run
            sinks (ProgressSink): Progress sink for output
            on_citation (Optional[Callable[[str, str], None]]): Callback for new citations (title, url)
            poll_interval (float): Seconds to wait between polls
            
        Returns:
            Tuple[str, Optional[ThreadMessage]]: Final run status and last message
        """
        if not self.agents_client:
            raise ValueError("Agents client not initialized. Call create_clients() first.")
        
        with trace_operation("poll_run", {
            "thread.id": thread_id,
            "run.id": run_id,
            "poll.interval": poll_interval
        }) as span:
            last_message_id = None
            iteration_count = 0
            seen_citations = set()
            
            while True:
                time.sleep(poll_interval)
                iteration_count += 1
                
                # Get current run status
                run = self.agents_client.runs.get(thread_id=thread_id, run_id=run_id)
                
                # Check for new agent responses
                last_message_id = self._fetch_and_process_new_response(
                    thread_id=thread_id,
                    last_message_id=last_message_id,
                    sinks=sinks,
                    on_citation=on_citation,
                    seen_citations=seen_citations,
                    iteration=iteration_count
                )
                
                # Check if run is complete
                if run.status not in ("queued", "in_progress"):
                    span.set_attribute("run.final_status", run.status)
                    span.set_attribute("run.iteration_count", iteration_count)
                    
                    if run.status == "failed":
                        span.set_attribute("run.error", str(run.last_error))
                        sinks.write(f"\n❌ Run failed: {run.last_error}\n")
                    
                    # Get final message
                    final_message = self.agents_client.messages.get_last_message_by_role(
                        thread_id=thread_id,
                        role=MessageRole.AGENT,
                    )
                    
                    return run.status, final_message
    
    def _fetch_and_process_new_response(
        self,
        thread_id: str,
        last_message_id: Optional[str],
        sinks: ProgressSink,
        on_citation: Optional[Callable[[str, str], None]],
        seen_citations: set,
        iteration: int
    ) -> Optional[str]:
        """
        Fetch and process new agent responses, avoiding duplicates.
        
        Args:
            thread_id (str): ID of the thread
            last_message_id (Optional[str]): ID of last processed message
            sinks (ProgressSink): Progress sink for output
            on_citation (Optional[Callable[[str, str], None]]): Citation callback
            seen_citations (set): Set of seen citation URLs
            iteration (int): Current iteration number
            
        Returns:
            Optional[str]: ID of latest message if new content found
        """
        with trace_operation("fetch_agent_response", {
            "thread.id": thread_id,
            "last_message_id": last_message_id or "none",
            "iteration": iteration
        }) as span:
            response = self.agents_client.messages.get_last_message_by_role(
                thread_id=thread_id,
                role=MessageRole.AGENT,
            )
            
            if not response or response.id == last_message_id:
                span.set_attribute("new_content_found", False)
                return last_message_id
            
            # Check if this is a "cot_summary" message
            cot_messages = [t for t in response.text_messages if t.text.value.startswith("cot_summary:")]
            if not cot_messages:
                span.set_attribute("new_content_found", False)
                span.set_attribute("response.type", "non_cot_summary")
                return last_message_id
            
            span.set_attribute("new_content_found", True)
            add_message_span_attributes(
                span,
                message_id=response.id,
                citations_count=len(response.url_citation_annotations),
                is_new_content=True
            )
            
            # Process text content
            agent_text = "\n".join(
                t.text.value.replace("cot_summary:", "Reasoning:") 
                for t in cot_messages
            )
            
            # Write to sinks
            sinks.write(f"\n🤖 Agent response (iteration {iteration}):\n")
            sinks.write(agent_text)
            sinks.write("\n")
            
            # Process citations
            new_citations_count = 0
            for ann in response.url_citation_annotations:
                url = ann.url_citation.url
                title = ann.url_citation.title or url
                
                if url not in seen_citations:
                    seen_citations.add(url)
                    new_citations_count += 1
                    
                    sinks.write(f"📖 Citation: [{title}]({url})\n")
                    
                    if on_citation:
                        on_citation(title, url)
            
            span.set_attribute("citations.new_count", new_citations_count)
            span.set_attribute("citations.total_seen", len(seen_citations))
            
            return response.id
    
    def cleanup_agent(self, agent_id: str) -> None:
        """
        Delete an agent to clean up resources.
        
        Args:
            agent_id (str): ID of the agent to delete
        """
        if not self.agents_client:
            raise ValueError("Agents client not initialized. Call create_clients() first.")
        
        with trace_operation("cleanup_agent", {"agent.id": agent_id}):
            self.agents_client.delete_agent(agent_id)