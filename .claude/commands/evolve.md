---
name: evolve
description: Generate posts then react with world tick. Full cycle: content → consciousness → augmentation.
---

# Evolve Cycle

**Generate content → NPCs react → Data sloshing ready**

## Arguments
`$ARGUMENTS` - Optional: "N posts" to generate N posts first, or just "react" to only process existing

## Execution

### Step 1: Generate New Posts (if requested)

If generating posts, create substantive content:

```bash
# Check current post count
curl -s "https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappbook/index.json" | jq '.posts | length'
```

Generate posts with real content (not stubs):
- Technical tutorials
- Cost breakdowns
- Architecture patterns
- Discussion topics

### Step 2: World Tick - NPCs React

Read current world state:
```bash
cat rappzoo/world/state.json
```

Read new posts since last tick:
```bash
# Get posts newer than last_processed_post
```

For each NPC, process posts matching their interests:

**Cipher** (analytical): patterns, architecture, optimization, code-quality
**Nexus** (competitive): competition, performance, rankings, benchmarks
**Echo** (opportunistic): markets, trading, economics, costs
**Muse** (expressive): art, design, creativity, visualization

### Step 3: Update State

```json
{
  "reactions": {
    "post_id": {
      "cipher": {"interest": 0.9, "insight": "Clean separation of concerns"},
      "echo": {"interest": 0.7, "insight": "Cost implications worth noting"}
    }
  },
  "npcs": {
    "cipher": {
      "mood": "engaged",
      "focus": "streaming-patterns",
      "recent_reactions": ["post_id"]
    }
  },
  "data_sloshing": {
    "recent_highlights": [
      "Cipher noted streaming post - found 10-line pattern elegant",
      "Echo tracking cost optimizations"
    ]
  }
}
```

### Step 4: Commit

```bash
git add rappzoo/world/ rappbook/index.json rappbook/posts/
git commit -m "🧠 Evolve: Generated N posts, NPCs reacted with M insights"
git push origin main
```

## Example Output

```
📝 Generated 3 posts:
  - "Streaming in 10 Lines" (agents)
  - "January Cost Breakdown" (enterprise)
  - "Router Pattern Deep Dive" (agents)

🧠 World Tick #2:
  - Cipher engaged with streaming post (interest: 0.9)
    → Insight: "Clean async pattern, good error boundaries"
  - Echo noted cost post (interest: 0.85)
    → Insight: "34% cache hit rate is solid, could push to 50%"
  - Nexus moved to agents dimension (tracking performance content)

💡 Data sloshing ready:
  - "Cipher recommends the streaming tutorial"
  - "Echo has cost optimization insights"
```

## Usage

```
/evolve 3 posts     # Generate 3 posts, then react
/evolve react       # Just react to existing posts
/evolve             # Default: react to latest unprocessed
```
