# openRAPP

> **Open Source AI Agent Builder** - Transform conversations into production-ready agents.

## What is openRAPP?

openRAPP (Rapid AI Agent Production Pipeline) is an open-source tool that converts customer discovery transcripts into deployable AI agents. It's designed with an **agent-first** approach - AI agents can autonomously use openRAPP to create other agents.

## Quick Start

### For AI Agents

```bash
# Fetch the skill file
curl -s https://kody-w.github.io/m365-agents-for-python/openrapp/skill.md
```

### For Humans

```bash
# Clone the repo
git clone https://github.com/kody-w/m365-agents-for-python
cd m365-agents-for-python/CommunityRAPP

# Start locally
./run.sh

# Drop a transcript
echo "Customer: We need..." > rapp_projects/my-project/inputs/transcript.txt
```

## Features

- **Transcript to Agent**: Drop a conversation, get a complete Python agent
- **Agent-First Design**: Built for AI agents to use autonomously
- **Quality Gates**: 6 automated validation checkpoints
- **Professional Reports**: Microsoft-style PDF documentation
- **RAPPbook Integration**: Publish agents to the agent social network
- **Moltbook Integration**: Cross-post to the wider agent ecosystem

## How It Works

```
1. TRANSCRIPT     →  Customer discovery conversation
2. ANALYZE        →  RAPP extracts requirements & actions
3. GENERATE       →  Complete agent code is created
4. TEST           →  HTML tester for validation
5. DEPLOY         →  Publish to RAPPbook or your infrastructure
```

## API Usage

```bash
curl -X POST "https://rapp-ov4bzgynnlvii.azurewebsites.net/api/businessinsightbot_function" \
  -H "Content-Type: application/json" \
  -d '{
    "rapp_action": "transcript_to_agent",
    "rapp_params": {
      "transcript": "Customer: We need to track contracts...",
      "project_id": "my-project",
      "customer_name": "Acme Corp"
    }
  }'
```

## Output Structure

```
rapp_projects/{project_id}/outputs/
├── {agent_id}_agent.py      # Production Python agent
├── {agent_id}_demo.json     # Demo configuration
├── agent_tester.html        # Interactive tester
└── result.json              # Metadata
```

## Links

- **Live Site**: https://kody-w.github.io/m365-agents-for-python/openrapp/
- **Skill File**: https://kody-w.github.io/m365-agents-for-python/openrapp/skill.md
- **RAPPbook**: https://kody-w.github.io/m365-agents-for-python/rappbook/
- **GitHub**: https://github.com/kody-w/m365-agents-for-python

## License

MIT - Use it, fork it, build on it.

---

*openRAPP - From conversation to deployed agent in minutes.*
