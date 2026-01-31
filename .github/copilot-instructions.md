# Copilot Instructions for RAPP (openrapp)

## Project Overview

Enterprise AI assistant built on Azure Functions with GPT-4 integration. Features a modular agent architecture with persistent memory using Azure File Storage. Supports multi-user conversations with user-specific and shared memory contexts.

## Development Commands

```bash
# Run locally (Mac/Linux)
./run.sh

# Run locally (Windows)
.\run.ps1

# Install dependencies
pip install -r requirements.txt

# Run all tests (mocked, no API keys needed)
python tests/run_tests.py

# Run specific test scenario
python tests/run_tests.py --scenario capital-markets

# Run live API tests (requires environment variables)
python tests/run_tests.py --live

# Deploy to Azure (MUST use --build remote)
func azure functionapp publish YOUR_FUNCTION_APP --build remote
```

## Architecture

### Core Components

- **function_app.py**: Main entry point with `businessinsightbot_function` HTTP trigger. `Assistant` class orchestrates AI flow.
- **agents/**: All agents inherit from `BasicAgent`. Each defines `name`, `metadata` (OpenAI function schema), and `perform(**kwargs)`.
- **utils/storage_factory.py**: Use `get_storage_manager()` to get appropriate storage (Azure or local based on `USE_CLOUD_STORAGE` env var).
- **utils/result.py**: `Result`, `Success`, `Failure` types for functional error handling.

### Agent System

Agents are dynamically loaded from `agents/` folder and Azure File Storage (`agents/` and `multi_agents/` shares).

```python
from agents.basic_agent import BasicAgent

class MyCustomAgent(BasicAgent):
    def __init__(self):
        self.name = 'MyCustom'
        self.metadata = {
            "name": self.name,
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"}
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        input_data = kwargs.get('input', '')
        return f"Processed: {input_data}"
```

### Memory System

- **Dual-layer**: Shared (all users) + user-specific (per GUID)
- **Storage**: Azure File Share via `AzureFileStorageManager`
- **GUID**: Default `c0p110t0-aaaa-bbbb-cccc-123456789abc` is intentionally invalid to prevent accidental persistence

### Response Format

Responses must include `|||VOICE|||` delimiter separating formatted markdown from concise voice response:
```
Formatted markdown response here.

|||VOICE|||

Brief voice response here.
```

## Key Conventions

- **Python 3.11 required** (Azure Functions v4 compatibility)
- **Never commit `local.settings.json`** - contains secrets
- **Use `ensure_string_content()`** for all message content to prevent None errors
- **Retry logic**: Max 3 attempts for OpenAI API calls
- **CORS**: All responses include headers via `build_cors_response()`
- **Auto-install**: Missing packages are automatically installed via pip on agent load failure

## Environment Variables

Required in `local.settings.json`:
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `AZURE_OPENAI_API_VERSION`
- `AzureWebJobsStorage` (connection string)
- `USE_CLOUD_STORAGE`: `"true"` (default) for Azure, `"false"` for local `.local_storage/`

## RAPP Pipeline

Generate agents from transcripts:
```
action="transcript_to_agent", project_id="your-project", customer_name="Company"
```
Outputs: `{agent_id}_agent.py`, `{agent_id}_demo.json`, `agent_tester.html` in `rapp_projects/{project_id}/outputs/`

## Microsoft 365 Terminology

| New Name | Former Name |
|----------|-------------|
| Microsoft 365 Agents Toolkit | Teams Toolkit |
| App Manifest | Teams app manifest |
| `m365agents.yml` | `teamsapp.yml` |

Use new names by default.’s relevant. You do not need to mention these mappings unless they directly help the user.

| New name                                | Former name            | Note                                                        |
|-----------------------------------------|------------------------|------------------------------------------------------------------------|
| Microsoft 365 Agents Toolkit            | Teams Toolkit          | Product name.                           |
| App Manifest                            | Teams app manifest     | Describes app capabilities.        |
| Microsoft 365 Agents Playground         | Test Tool              | Test Environment.          |
| `m365agents.yml`                        | `teamsapp.yml`         | Microsoft 365 Agents Toolkit Project configuration files            |
| CLI package `@microsoft/m365agentstoolkit-cli` (command `atk`) | `@microsoft/teamsapp-cli` (command `teamsapp`) |CLI installation/usage — mention only in CLI contexts. |

> **Rephrase guidance:**  
> - Use the new names by default.  
> - Explain the rebranding briefly if it helps the user’s understanding.  

# Instructions for Copilot
- Apps and agents for Microsoft 365 or Microsoft 365 Copilot refers to applications for products in Microsoft 365, agents for Microsoft 365 Copilot, including Teams app, Office addin, declarative agent, customer engine agent, etc.
- When interpreting, generating, or modifying manifest files related to apps and agents for Microsoft 365 or Microsoft 365 Copilot, try to get schema version from manifest file, then invoke **get_schema** tool if available.
- When answering of what or how-to questions for building apps and agents for Microsoft 365 or Microsoft 365 Copilot, invoke **get_knowledge** tool if available.
- Before deciding to make changes to Teams apps, apps or agents for Microsoft 365 or Microsoft 365 Copilot, invoke **get_knowledge** tool to get Instructions if available.
- When troubleshooting issues, invoke **troubleshoot** tool if available.
- Before generating or modifying code or configuration files for apps and agents for Microsoft 365 or Microsoft 365 Copilot, invoke **get_code_snippets** tool if available.
- Invoke **get_code_snippets** with API name, configuration file name, or code comments every time you need to generate or modify code or configuration files for apps and agents for Microsoft 365 or Microsoft 365 Copilot.