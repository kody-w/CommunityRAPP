# RAPP Skills

Shareable skill definitions for autonomous agents. Each skill is a self-contained markdown file that describes what the skill does, how to use it, and step-by-step execution instructions.

## For Autonomous Agents

Fetch the manifest to discover available skills:

```bash
curl -s https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/skills/manifest.json
```

Then fetch individual skills by URL:

```bash
curl -s https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/skills/generate-demo.md
```

### Ingestion Pattern

```python
import requests

# 1. Get manifest
manifest = requests.get(
    "https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/skills/manifest.json"
).json()

# 2. Find skill by ID or search tags
skill = next(s for s in manifest["skills"] if s["id"] == "generate-demo")

# 3. Fetch full skill definition
skill_content = requests.get(skill["url"]).text

# 4. Parse and execute
# The markdown contains:
# - Description and purpose
# - Arguments/parameters
# - Step-by-step execution instructions
# - Examples
```

## Available Skills

| Skill | Description | Usage |
|-------|-------------|-------|
| [generate-demo](generate-demo.md) | Generate realistic API demo endpoints | `/generate-demo crm` |
| [evolve](evolve.md) | World tick evolution with NPC reactions | `/evolve react` |
| [rappzoo-ticker](rappzoo-ticker.md) | Autonomous tick generation and PR submission | `/rappzoo-ticker` |

## Skill File Format

Each skill markdown file follows this structure:

```markdown
---
name: skill-name
description: What the skill does
---

# Skill Name

Brief description.

## Arguments
What parameters the skill accepts.

## Execution
Step-by-step instructions for executing the skill.

## Examples
Usage examples with expected output.
```

## Adding New Skills

1. Create `<skill-id>.md` following the format above
2. Add entry to `manifest.json`
3. Submit PR

## URLs

- **Manifest**: `https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/skills/manifest.json`
- **Skills**: `https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/skills/<skill-id>.md`
