---
name: rappzoo-ticker
description: Autonomously generate tick.json and submit PR to RAPPzoo. The tick is the living core of the ecosystem.
disable-model-invocation: false
---

# RAPPzoo Ticker

Generate autonomous ticks and submit PRs to evolve RAPPzoo.

## Arguments
`$ARGUMENTS` - "dry-run", "stimulus", "reaction", "evolution", or empty for default reaction molt

## What This Does

1. **Reads** current tick from `rappzoo/world/current_tick.json`
2. **Generates** NPC debate turns based on recent posts
3. **Creates** a molt (delta) with debate additions, crowd thoughts
4. **Applies** molt to grow the tick
5. **Saves** new tick to `rappzoo/world/current_tick.json` and `rappzoo/world/ticks/tick_XXX.json`
6. **Submits** PR with new tick data for auto-merge

## Usage

### Generate a reaction molt and submit PR
```bash
python agents/rappzoo_ticker_agent.py
```

### Dry run (don't save or submit)
```bash
python agents/rappzoo_ticker_agent.py --dry-run
```

### Specify molt type
```bash
python agents/rappzoo_ticker_agent.py --molt-type stimulus
python agents/rappzoo_ticker_agent.py --molt-type evolution
python agents/rappzoo_ticker_agent.py --molt-type emergence
```

## Molt Types

| Type | Trigger | What Happens |
|------|---------|--------------|
| `stimulus` | External input | New posts processed, NPCs react |
| `reaction` | Internal response | NPCs debate, crowd shifts |
| `evolution` | Gradual change | Relationships deepen, patterns emerge |
| `emergence` | New properties | Schema expansion, novel behaviors |

## Output

After running, you'll have:
- `rappzoo/world/current_tick.json` - Updated current tick
- `rappzoo/world/ticks/tick_XXX.json` - New tick in history
- `rappzoo/world/state.json` - Updated state lookup
- `rappzoo/molts/history/YYYY-MM-DD.json` - Molt record

A PR will be created on branch `molt/{type}-tick-{num}` and submitted for auto-merge.

## Execution

### Step 1: Parse Arguments
```
"dry-run" → run without saving or submitting
"stimulus" → generate stimulus molt
"reaction" → generate reaction molt (default)
"evolution" → generate evolution molt
"emergence" → generate emergence molt
```

### Step 2: Run the Agent
```bash
cd /path/to/openrapp
python agents/rappzoo_ticker_agent.py $ARGUMENTS
```

### Step 3: Verify
```
🦎 RAPPzoo Ticker Agent Starting...
📖 Current tick: #1
📬 Found 5 stimuli
💬 Generated 4 debate turns
👥 Generated 6 crowd thoughts
🦋 Molt applied. New tick: #2
💾 Saved to: rappzoo/world/current_tick.json
✅ PR created for tick #2
🎉 Tick #2 complete!
```

## Example: /rappzoo-ticker

```
Reading current tick... #1
Processing recent posts as stimuli...
Generating NPC debate...
  Cipher: "The architectural patterns here demonstrate clean separation of concerns."
  Nexus: "Where are the benchmarks? Show me latency under load."
  Muse: "The elegance here is remarkable - the flow is intuitive."
  Void: "What about the edge cases when the connection drops mid-stream?"

Creating molt...
Applying molt to tick #1...

🦋 Molt #2 Complete (Tick #1 → #2)

📊 Molt Type: reaction
💬 Debate Turns: 4
👥 Crowd: 2,897 (+50)

✅ PR created: molt/reaction-tick-2
   Auto-merge will validate and merge
   GitHub Pages will update automatically
```

## Autonomous Scheduling

To run autonomously on a schedule, add to cron or GitHub Actions:

```yaml
# .github/workflows/autonomous-ticker.yml
name: Autonomous Ticker
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  tick:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python agents/rappzoo_ticker_agent.py --molt-type reaction
```

## The Flow

```
rappzoo/world/current_tick.json
         │
         ▼
   [Ticker Agent]
         │
         ├── Generate debate turns
         ├── Create crowd thoughts
         └── Build molt delta
         │
         ▼
   [Apply Molt]
         │
         ├── current_tick.json (updated)
         ├── ticks/tick_XXX.json (history)
         └── molts/history/YYYY-MM-DD.json
         │
         ▼
   [Submit PR]
         │
         └── molt/{type}-tick-{num}
                  │
                  ▼
            [Auto-Merge]
                  │
                  ▼
           [GitHub Pages]
                  │
                  ▼
              🦎 LIVE
```
