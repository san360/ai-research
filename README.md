# Azure Agents Deep Research UI

🔬 **Comprehensive research powered by Azure AI Agents with live progress tracking**

A Streamlit-based web application that provides an interactive interface for Azure Agents Deep Research operations, featuring real-time progress updates, live citation tracking, and downloadable research reports.

## Features

- 🚀 **Live Progress Tracking**: Real-time updates as research progresses
- 📖 **Dynamic Citations**: Citations discovered and displayed in real-time
- 📄 **Formatted Reports**: Final reports with superscript citations and proper formatting
- 💾 **File Outputs**: Automatic saving of progress logs and final reports
- 📊 **Research Metrics**: Comprehensive statistics about the research session
- 🔧 **Configurable Settings**: Environment variables with UI overrides
- 📥 **Download Capabilities**: Download both the final report and progress logs
- 🔍 **OpenTelemetry Integration**: Full telemetry and tracing for observability

## Project Structure

```
deep_research_ui/
├── app.py                          # Streamlit UI entrypoint
├── services/
│   └── agents_service.py           # Azure Agents interactions + polling
├── utils/
│   ├── citations.py                # Citation conversion utilities
│   └── logging_sinks.py            # Progress sink system
├── reports/
│   └── report_builder.py           # Research summary creation
├── telemetry/
│   └── tracing.py                  # OpenTelemetry configuration
└── tests/
    ├── test_citations.py           # Citation utility tests
    └── test_logging_sinks.py       # Logging sink tests

# Legacy
main.py                             # Original sample (preserved for reference)
```

## Requirements

- Python 3.10+
- Azure subscription with AI Projects and Bing Search resources
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone or download this project
2. Install dependencies using [uv](https://github.com/astral-sh/uv) (recommended):
   ```bash
   uv pip install -r requirements.txt
   ```
   
   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
PROJECT_ENDPOINT=<your-azure-ai-project-endpoint>
MODEL_DEPLOYMENT_NAME=<your-model-deployment-name>
DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME=<your-deep-research-model-deployment-name>
BING_RESOURCE_NAME=<your-bing-resource-name>
```

**Where to find these values:**

- `PROJECT_ENDPOINT`: Azure AI Foundry portal → Your project → Overview → Project details
- `MODEL_DEPLOYMENT_NAME`: Azure AI Foundry portal → Your project → Deployments → Chat model name
- `DEEP_RESEARCH_MODEL_DEPLOYMENT_NAME`: Azure AI Foundry portal → Your project → Deployments → Research model name
- `BING_RESOURCE_NAME`: Azure portal → Your Bing Search resource → Overview → Name

## Usage

### Running the Streamlit App

1. **Start the application:**
   ```bash
   streamlit run deep_research_ui/app.py
   ```

2. **Configure your research:**
   - Enter your research topic in the text input
   - Optionally specify additional instructions
   - Click "Start Research" to begin

3. **Monitor progress:**
   - Watch live progress logs appear in real-time
   - See citations discovered during research
   - Monitor the research status and completion

4. **Review results:**
   - View the formatted research report in the UI
   - Download the complete report as markdown
   - Download progress logs for detailed analysis

### Command Line (Legacy)

The original command-line interface is preserved in `main.py`:
```bash
uv run main.py
```

## Output Files

The application creates several output files for auditability:

- `research_progress.txt`: Real-time progress logs and incremental findings
- `research_report.md`: Complete research report with citations and formatting
- Telemetry traces: Sent to Azure Monitor for observability

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Services Layer**: `services/agents_service.py` - Handles all Azure Agents interactions
- **Utilities**: `utils/` - Citation processing and flexible logging sinks
- **Reports**: `reports/report_builder.py` - Research summary generation
- **Telemetry**: `telemetry/tracing.py` - OpenTelemetry configuration
- **UI Layer**: `deep_research_ui/app.py` - Streamlit web interface
- **Testing**: `tests/` - Comprehensive unit test coverage

## Troubleshooting

### Common Issues

**Authentication Errors**: Ensure your Azure credentials are properly configured:
```bash
az login
```

**Missing Environment Variables**: Verify all required variables are set in your `.env` file.

**Import Errors**: Make sure all dependencies are installed:
```bash
uv pip install -r requirements.txt
```

**Streamlit Port Issues**: If port 8501 is in use, specify a different port:
```bash
streamlit run deep_research_ui/app.py --server.port 8502
```

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export STREAMLIT_LOGGER_LEVEL=debug
```

## References

- See `research_report.md` for a sample output and citations
- For more details, refer to the official [Deep Research Tool documentation](https://aka.ms/agents-deep-research)
- [Azure AI Agents documentation](https://docs.microsoft.com/azure/ai-services/agents/)
- [Streamlit documentation](https://docs.streamlit.io/)
