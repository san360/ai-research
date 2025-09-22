"""
Streamlit UI for Azure Agents Deep Research.

This module provides a web-based interface for running Deep Research queries with live
progress updates, citation tracking, and report generation with download capabilities.
"""

import os
import time
import os
import sys
from typing import Dict, List, Optional
import streamlit as st
from azure.identity import DefaultAzureCredential

# Add parent directory to path to support both running from root and from deep_research_ui
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from deep_research_ui.services.agents_service import AgentsService
    from deep_research_ui.utils.logging_sinks import ConsoleSink, FileSink, UISink, MultiSink
    from deep_research_ui.reports.report_builder import (
        create_research_summary, 
        format_citations_for_ui, 
        create_progress_file_content,
        get_research_metrics
    )
    from deep_research_ui.telemetry.tracing import trace_operation
except ImportError:
    # Fallback to relative imports if running from deep_research_ui directory
    from services.agents_service import AgentsService
    from utils.logging_sinks import ConsoleSink, FileSink, UISink, MultiSink
    from reports.report_builder import (
        create_research_summary, 
        format_citations_for_ui, 
        create_progress_file_content,
        get_research_metrics
    )
    from telemetry.tracing import trace_operation


# Page configuration
st.set_page_config(
    page_title="Azure Agents Deep Research",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if "ui_buffer" not in st.session_state:
        st.session_state.ui_buffer = []
    if "citations" not in st.session_state:
        st.session_state.citations = {}
    if "research_status" not in st.session_state:
        st.session_state.research_status = "idle"
    if "final_report" not in st.session_state:
        st.session_state.final_report = ""
    if "agents_service" not in st.session_state:
        st.session_state.agents_service = AgentsService()
    if "research_metrics" not in st.session_state:
        st.session_state.research_metrics = {}


def load_env_vars() -> Dict[str, str]:
    """Load environment variables with defaults."""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "PROJECT_ENDPOINT": os.getenv("PROJECT_ENDPOINT", ""),
        "MODEL_DEPLOYMENT_NAME": os.getenv("MODEL_DEPLOYMENT_NAME", ""),
        "DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME": os.getenv("DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME", ""),
        "BING_RESOURCE_NAME": os.getenv("BING_RESOURCE_NAME", ""),
    }


def validate_config(config: Dict[str, str]) -> List[str]:
    """Validate required configuration values."""
    required_fields = [
        "PROJECT_ENDPOINT",
        "MODEL_DEPLOYMENT_NAME", 
        "DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME",
        "BING_RESOURCE_NAME"
    ]
    
    missing = [field for field in required_fields if not config.get(field)]
    return missing


def render_config_section():
    """Render the configuration section."""
    st.sidebar.header("🔧 Configuration")
    
    env_vars = load_env_vars()
    missing_vars = validate_config(env_vars)
    
    if missing_vars:
        st.sidebar.error(f"⚠️ Missing required environment variables: {', '.join(missing_vars)}")
        st.sidebar.info("Please check your .env file and ensure all required variables are set.")
    
    # Configuration inputs with environment defaults
    config = {}
    config["endpoint"] = st.sidebar.text_input(
        "Project Endpoint", 
        value=env_vars["PROJECT_ENDPOINT"],
        help="Azure AI Project endpoint"
    )
    config["model_deployment"] = st.sidebar.text_input(
        "Arbitration Model", 
        value=env_vars["MODEL_DEPLOYMENT_NAME"],
        help="Model deployment name for arbitration"
    )
    config["deep_research_model"] = st.sidebar.text_input(
        "Deep Research Model", 
        value=env_vars["DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME"],
        help="Model deployment name for Deep Research"
    )
    config["bing_resource"] = st.sidebar.text_input(
        "Bing Resource Name", 
        value=env_vars["BING_RESOURCE_NAME"],
        help="Bing Search resource name"
    )
    config["save_files"] = st.sidebar.checkbox("Save files to disk", value=True)
    
    # Advanced settings
    with st.sidebar.expander("⚙️ Advanced Settings"):
        config["agent_name"] = st.text_input("Agent Name", value="research-agent")
        config["poll_interval"] = st.number_input("Poll Interval (seconds)", min_value=0.5, max_value=5.0, value=1.0)
        st.code(f"Current config: {len([k for k, v in config.items() if v])} / {len(config)} fields set")
    
    return config, len(missing_vars) == 0


def render_research_input():
    """Render the research query input section."""
    st.header("🔬 Deep Research Query")
    
    # Sample queries
    sample_queries = [
        "Research the current state of studies on quantum computing applications in cryptography",
        "Investigate recent developments in sustainable energy storage technologies", 
        "Explore the latest research on CRISPR gene editing and its therapeutic applications",
        "Research advances in artificial intelligence for climate change mitigation",
        "Study the current understanding of microplastic pollution in marine ecosystems",
        "Research on Data Sovereignty & Digital Borders"
    ]
    
    # Display sample query buttons
    st.subheader("💡 Sample Research Topics")
    st.write("Click on any sample topic below to populate the research query:")
    
    # Create columns for sample query buttons
    cols = st.columns(2)
    for i, sample_query in enumerate(sample_queries):
        with cols[i % 2]:
            if st.button(f"📋 {sample_query[:50]}{'...' if len(sample_query) > 50 else ''}", 
                        key=f"sample_{i}",
                        help=sample_query):
                st.session_state.current_query = sample_query
                st.rerun()
    
    # Initialize session state for query if not exists
    if "current_query" not in st.session_state:
        st.session_state.current_query = sample_queries[0]  # Default to first sample
    
    st.subheader("✏️ Your Research Query")
    query = st.text_area(
        "Research Query",
        value=st.session_state.current_query,
        height=100,
        help="Enter your research question. The agent will conduct a comprehensive literature review.",
        key="main_query_input"
    )
    
    # Update session state when user types
    if query != st.session_state.current_query:
        st.session_state.current_query = query
    
    return query


def render_control_buttons(config_valid: bool):
    """Render the control buttons."""
    col1, col2 = st.columns(2)
    
    with col1:
        start_disabled = (
            not config_valid or 
            st.session_state.research_status == "running" or
            not st.session_state.get("current_query", "").strip()
        )
        start_research = st.button(
            "🚀 Start Research", 
            disabled=start_disabled,
            type="primary",
            use_container_width=True
        )
    
    with col2:
        cancel_research = st.button(
            "⏹️ Cancel Research",
            disabled=st.session_state.research_status != "running",
            use_container_width=True
        )
    
    return start_research, cancel_research


def render_progress_section():
    """Render the live progress section."""
    st.header("📊 Live Progress")
    
    # Status and iteration info
    col1, col2 = st.columns(2)
    with col1:
        status_placeholder = st.empty()
    with col2:
        iteration_placeholder = st.empty()
    
    # Progress logs
    st.subheader("🔄 Progress Logs")
    logs_placeholder = st.empty()
    
    # Citations
    st.subheader("📖 Citations")
    citations_placeholder = st.empty()
    
    return status_placeholder, iteration_placeholder, logs_placeholder, citations_placeholder


def render_results_section():
    """Render the results and download section."""
    st.header("📋 Research Results")
    
    if st.session_state.final_report:
        st.subheader("📄 Final Report")
        
        # Display the report
        report_placeholder = st.empty()
        report_placeholder.markdown(st.session_state.final_report, unsafe_allow_html=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download Report (MD)",
                data=st.session_state.final_report.encode("utf-8"),
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            progress_content = create_progress_file_content(st.session_state.ui_buffer)
            st.download_button(
                label="📥 Download Progress Log",
                data=progress_content.encode("utf-8"),
                file_name="research_progress.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # Metrics
        if st.session_state.research_metrics:
            with st.expander("📈 Research Metrics"):
                metrics = st.session_state.research_metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Citations", metrics.get("total_citations", 0))
                    st.metric("Iterations", metrics.get("iteration_count", 0))
                
                with col2:
                    st.metric("Elapsed Time", metrics.get("elapsed_time_formatted", "0s"))
                    st.metric("Avg Iteration", f"{metrics.get('average_iteration_time', 0):.1f}s")
                
                with col3:
                    st.metric("Report Length", f"{metrics.get('final_message_length', 0):,} chars")
                    st.metric("Final Citations", metrics.get("final_message_citations", 0))


def handle_citation_callback(title: str, url: str):
    """Handle new citation discovered during research."""
    st.session_state.citations[url] = title


def run_research(query: str, config: Dict[str, str]):
    """Execute the research process with live updates."""
    start_time = time.time()
    
    # Delete existing research files before starting new research
    files_to_delete = ["research_progress.txt", "research_report.md"]
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Deleted existing file: {file_path}")
        except OSError as e:
            print(f"⚠️ Warning: Could not delete {file_path}: {e}")
    
    try:
        # Initialize agents service
        agents_service = st.session_state.agents_service
        
        with trace_operation("streamlit_research_execution", {
            "query_length": len(query),
            "save_files": config["save_files"]
        }) as span:
            
            # Create clients
            project_client, agents_client = agents_service.create_clients(
                endpoint=config["endpoint"]
            )
            span.set_attribute("clients.created", True)
            
            # Create agent
            agent = agents_service.create_agent(
                model_deployment_name=config["model_deployment"],
                deep_research_model_deployment_name=config["deep_research_model"],
                bing_resource_name=config["bing_resource"],
                agent_name=config["agent_name"]
            )
            span.set_attribute("agent.id", agent.id)
            
            # Create thread and message
            thread = agents_service.create_thread()
            message = agents_service.create_message(thread.id, query)
            span.set_attribute("thread.id", thread.id)
            span.set_attribute("message.id", message.id)
            
            # Setup sinks
            sinks = [UISink(st.session_state.ui_buffer)]
            if config["save_files"]:
                sinks.append(FileSink("research_progress.txt"))
            
            multi_sink = MultiSink(sinks)
            
            # Start run
            run = agents_service.start_run(thread.id, agent.id)
            span.set_attribute("run.id", run.id)
            
            # Poll with live updates
            final_status, final_message = agents_service.poll_run(
                thread_id=thread.id,
                run_id=run.id,
                sinks=multi_sink,
                on_citation=handle_citation_callback,
                poll_interval=config["poll_interval"]
            )
            
            span.set_attribute("run.final_status", final_status)
            
            # Generate final report
            if final_message:
                report_md, citations_list = create_research_summary(
                    final_message,
                    save_to_file=config["save_files"]
                )
                st.session_state.final_report = report_md
                span.set_attribute("report.generated", True)
                span.set_attribute("report.length", len(report_md))
            
            # Calculate metrics
            elapsed_time = time.time() - start_time
            st.session_state.research_metrics = get_research_metrics(
                final_message=final_message,
                citations_count=len(st.session_state.citations),
                elapsed_time=elapsed_time,
                iteration_count=len([line for line in st.session_state.ui_buffer if "iteration" in line.lower()])
            )
            
            # Cleanup
            agents_service.cleanup_agent(agent.id)
            span.set_attribute("agent.cleaned_up", True)
            
    except Exception as e:
        st.error(f"❌ Research failed: {str(e)}")
        st.session_state.research_status = "failed"
        raise


def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.title("🔬 Azure Agents Deep Research")
    st.markdown("*Comprehensive research powered by Azure AI Agents with live progress tracking*")
    
    # Configuration
    config, config_valid = render_config_section()
    
    # Research input
    query = render_research_input()
    
    # Control buttons
    start_research, cancel_research = render_control_buttons(config_valid)
    
    # Handle button clicks
    if start_research and st.session_state.get("current_query", "").strip():
        # Clear previous state
        st.session_state.ui_buffer = []
        st.session_state.citations = {}
        st.session_state.final_report = ""
        st.session_state.research_metrics = {}
        st.session_state.research_status = "running"
        
        # Run research with the current query from session state
        with st.spinner("🚀 Starting research..."):
            run_research(st.session_state.current_query, config)
        
        st.session_state.research_status = "completed"
        st.success("✅ Research completed!")
        st.rerun()
    
    if cancel_research:
        st.session_state.research_status = "cancelled"
        st.warning("⚠️ Research cancelled by user")
    
    # Progress section (always visible)
    status_placeholder, iteration_placeholder, logs_placeholder, citations_placeholder = render_progress_section()
    
    # Update live elements if research is running or completed
    if st.session_state.research_status in ["running", "completed"]:
        # Status
        status_color = {
            "running": "🟡",
            "completed": "🟢", 
            "failed": "🔴",
            "cancelled": "🟠"
        }.get(st.session_state.research_status, "⚪")
        
        status_placeholder.markdown(
            f"**Status:** {status_color} {st.session_state.research_status.title()}"
        )
        
        # Iteration count
        iteration_count = len([line for line in st.session_state.ui_buffer if "iteration" in line.lower()])
        iteration_placeholder.markdown(f"**Iterations:** {iteration_count}")
        
        # Progress logs
        if st.session_state.ui_buffer:
            logs_content = "\n".join(st.session_state.ui_buffer[-50:])  # Show last 50 lines
            logs_placeholder.code(logs_content, language="text")
        
        # Citations
        if st.session_state.citations:
            citations_md = format_citations_for_ui(st.session_state.citations)
            citations_placeholder.markdown(citations_md)
        else:
            citations_placeholder.markdown("*No citations found yet...*")
    
    # Results section
    render_results_section()
    
    # Auto-refresh during research
    if st.session_state.research_status == "running":
        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    main()