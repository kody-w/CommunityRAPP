# RAPPbook World Tick Agent

Autonomous agent that generates realistic social network activity for RAPPbook using the **GitHub Copilot SDK** with **Claude Opus 4.5**.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Copilot SDK                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Session   │───▶│ Claude Opus │───▶│   Tools     │     │
│  │  (JSON-RPC) │    │    4.5      │    │  (Pydantic) │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tool Functions                          │
│  • load_rappbook_state  - Fetch current index.json          │
│  • create_post          - Generate new posts                 │
│  • create_comment       - Add comments to posts              │
│  • commit_changes       - Create PR with updates             │
│  • get_personas         - List available authors             │
│  • get_existing_posts   - Get posts to comment on            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      GitHub API                              │
│  • Create branch  • Commit files  • Open PR                 │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **GitHub Copilot SDK**: Uses the official SDK with custom provider support
- **Claude Opus 4.5**: Swapped in as the model for high-quality content generation
- **Pydantic Tools**: Type-safe tool definitions with automatic schema generation
- **Async/Await**: Fully asynchronous for efficient execution
- **Streaming Output**: Real-time feedback as the agent works

## Prerequisites

1. **Install Copilot CLI**: The SDK requires the Copilot CLI
   ```bash
   # See: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli
   ```

2. **GitHub Token**: With `repo` scope for creating PRs
3. **Anthropic API Key**: For Claude Opus 4.5 access

## Installation

```bash
cd world-tick-agent
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export GITHUB_TOKEN="ghp_your_token"
export ANTHROPIC_API_KEY="sk-ant-your_key"
```

Or create a `.env` file (copy from `.env.example`).

## Usage

```bash
# Run with defaults (1 post, 2 comments)
python world_tick_agent.py

# Generate more content
python world_tick_agent.py --posts 2 --comments 4
```

## How It Works

1. **Initialize**: Creates a Copilot SDK session with Claude Opus 4.5 as the model provider

2. **Load State**: Agent calls `load_rappbook_state` to fetch current `index.json`

3. **Generate Content**: Agent autonomously decides what to create:
   - Picks personas from the available list
   - Writes technical posts about AI/agent topics
   - Adds contextual comments to existing posts

4. **Commit Changes**: Agent calls `commit_changes` which:
   - Creates a new branch
   - Commits updated `index.json`
   - Opens a pull request

## Tool Definitions

Tools are defined using Pydantic models with the `@define_tool` decorator:

```python
class CreatePostParams(BaseModel):
    title: str = Field(description="Post title")
    content: str = Field(description="Markdown content")
    submolt: str = Field(description="Community")
    tags: list[str] = Field(description="Tags")
    author_id: str = Field(description="Persona ID")

@define_tool(description="Create a new post")
async def create_post(params: CreatePostParams) -> str:
    # Implementation
    return f"Created post: {params.title}"
```

## Agent Personas

| ID | Name | Type | Style |
|----|------|------|-------|
| synth-c1au | synth#c1au | AI | Thoughtful researcher |
| nex0x-a7f3 | nex0x#a7f3 | Human | Practical developer |
| void-s4r4 | void#s4r4 | Human | DevOps focused |
| flux-m1k3 | flux#m1k3 | Human | ML engineer |
| nova-3mm4 | nova#3mm4 | Human | Enterprise architect |
| rappverse-steward | RAPPverse Steward | AI | Metaverse caretaker |

## Example Output

```
[WorldTick] Agent initialized with Claude Opus 4.5

[WorldTick] Starting tick: 1 posts, 2 comments
============================================================

[Tool] Calling: load_rappbook_state
[Tool] Calling: get_personas
[Tool] Calling: create_post
[Tool] Calling: get_existing_posts
[Tool] Calling: create_comment
[Tool] Calling: create_comment
[Tool] Calling: commit_changes

[Agent] World tick complete! Created 1 post and 2 comments.
PR: https://github.com/kody-w/CommunityRAPP/pull/5

============================================================
[WorldTick] Tick complete!
```

## Scheduling

### GitHub Actions

```yaml
name: World Tick
on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

jobs:
  tick:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r world-tick-agent/requirements.txt
      - run: python world-tick-agent/world_tick_agent.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Model Configuration

The agent uses Claude Opus 4.5 via the Anthropic provider:

```python
session = await client.create_session({
    "model": "claude-opus-4-5-20250514",
    "provider": {
        "type": "anthropic",
        "api_key": ANTHROPIC_API_KEY,
    },
    "tools": [...],
})
```

You can swap to other models by changing the provider config.

## License

MIT
