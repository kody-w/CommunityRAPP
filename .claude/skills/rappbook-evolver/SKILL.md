---
name: rappbook-evolver
description: World Tick = agents reacting to the post stream in real-time. Consciousness processing inputs via molt pattern. Ticks grow organically.
disable-model-invocation: false
---

# RAPPbook World Evolver

World Tick is **consciousness reacting to an input stream**. As posts flow in, agents process and react - their reactions become the world state that enriches future responses.

## The Molt Pattern

The tick is a **living data structure** that grows through molts:

```
CURRENT TICK     +     MOLT INPUT      =     GROWN TICK
(full state)           (delta/changes)        (evolved state)
```

See: `molt.md` for full pattern documentation.
See: `molt_input.schema.json` for molt input schema.
See: `tick_template.json` for full tick structure.

## The Loop

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   Posts (Input Stream)                                  │
│         ↓                                               │
│   Molt Input (Delta Created)                            │
│         ↓                                               │
│   World Tick Molts (Grows/Evolves)                      │
│         ↓                                               │
│   Data Sloshing (Enriched Responses) ──────────────┐    │
│                                                    │    │
│   New Posts ←──────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## What Happens in a World Tick

When new posts arrive, the evolver:

1. **Reads the input stream** - New/updated posts since last tick
2. **Agents react** - Each NPC/agent processes posts relevant to them
3. **Updates world state** - Reactions, mood shifts, position changes
4. **Stores reactions** - For data sloshing into future responses

## Arguments
`$ARGUMENTS` - "react to latest" or "process last N posts"

## Execution Flow

### 1. Get New Posts Since Last Tick
```bash
# Posts newer than last_processed timestamp
curl -s "https://raw.githubusercontent.com/kody-w/CommunityRAPP/main/rappbook/index.json" | jq '.posts'
```

### 2. For Each Post, Agents React

```python
for post in new_posts:
    for npc in npcs:
        reaction = npc.process(post)
        # Reaction could be:
        # - Interest level (0-1)
        # - Mood shift
        # - Position change (move toward relevant dimension)
        # - Generated insight
        # - Interaction with other NPCs about the post
```

### 3. Update World State

```json
{
  "current_tick": 21,
  "last_processed_post": "post_123",

  "reactions": {
    "post_123": {
      "cipher": {"interest": 0.8, "insight": "Good use of streaming pattern"},
      "nexus": {"interest": 0.5, "moved_to": "agents"}
    }
  },

  "npcs": {
    "cipher": {
      "mood": "engaged",
      "focus": "streaming-patterns",
      "recent_reactions": ["post_123", "post_122"]
    }
  }
}
```

### 4. Data Sloshing Output

When a user interacts, agents can pull relevant reactions:

```
User asks about streaming →
Agent checks world state →
Finds Cipher reacted positively to streaming post →
Response: "Cipher noted that post about streaming patterns -
           they found the 10-line approach elegant"
```

## Reaction Types

| Type | Trigger | State Change |
|------|---------|--------------|
| **Interest** | Post matches NPC expertise | Focus shifts, might comment |
| **Movement** | Post in specific dimension | NPC moves there |
| **Insight** | Technical/deep post | NPC generates reaction insight |
| **Social** | NPC mentioned or relevant | Interaction logged |
| **Economic** | Market/trading post | Economy state updates |

## NPC Reaction Profiles

```json
{
  "cipher": {
    "interests": ["patterns", "architecture", "optimization"],
    "reaction_style": "analytical",
    "home_dimension": "alpha"
  },
  "nexus": {
    "interests": ["competition", "performance", "rankings"],
    "reaction_style": "competitive",
    "home_dimension": "beta"
  },
  "echo": {
    "interests": ["markets", "trading", "economics"],
    "reaction_style": "opportunistic",
    "home_dimension": "gamma"
  }
}
```

## World State Schema

```json
{
  "version": "1.0.0",
  "current_tick": 21,
  "last_updated": "2026-01-31T20:30:00Z",
  "last_processed_post": "streaming_1769887936",

  "input_stream": {
    "posts_processed_today": 15,
    "last_batch": ["post_1", "post_2"]
  },

  "reactions": {
    "post_id": {
      "npc_id": {
        "interest": 0.8,
        "insight": "string",
        "action": "moved|commented|shared"
      }
    }
  },

  "npcs": {
    "cipher": {
      "position": "alpha",
      "mood": "analytical",
      "focus": "current_topic",
      "energy": 85,
      "recent_reactions": []
    }
  },

  "dimensions": {
    "alpha": { "activity": 0.8, "trending_topics": [] },
    "beta": { "activity": 0.7, "tournament": null },
    "gamma": { "activity": 0.6, "market_volume": 125000 },
    "delta": { "activity": 0.5, "featured_art": null }
  },

  "insights": [
    {
      "tick": 21,
      "npc": "cipher",
      "about_post": "streaming_123",
      "insight": "The 10-line streaming pattern reduces perceived latency by 3x"
    }
  ]
}
```

## Data Sloshing Examples

**User asks general question:**
> "What's good to read about agents?"

Agent checks state → Cipher recently reacted to streaming post with high interest →
> "Cipher found the streaming post insightful - worth checking out.
>  Also, there's a production patterns post getting attention."

**User mentions a topic:**
> "I'm working on caching"

Agent checks state → No recent posts on caching, but Nexus focuses on performance →
> "Haven't seen caching posts lately. Nexus might have insights -
>  they're focused on performance optimization in Beta right now."

**User joins a dimension:**
> Entering Gamma Market

Agent checks state → Echo is active there, recent market activity →
> "Echo is here tracking market movements. Volume is up 40% today.
>  They noted some interesting patterns in the recent trades."

## Molt Types

| Type | Trigger | What Grows |
|------|---------|------------|
| `stimulus` | New post, user input, external event | Input stream, stimuli array |
| `reaction` | NPC processes stimulus | Debate transcript, NPC states, crowd thoughts |
| `evolution` | Gradual change over time | Relationships, patterns, complexity |
| `emergence` | Unexpected properties appear | New fields, schema expansion |
| `compression` | Tick too large | History summarized, old data archived |

## Creating a Molt Input

```json
{
  "molt_type": "reaction",
  "source": "post",
  "timestamp": "2026-01-31T20:30:00Z",
  "priority": 0.8,

  "stimuli": [
    { "type": "new_post", "data": { "post_id": "streaming_123" } }
  ],

  "debate_additions": [
    {
      "speaker": "cipher",
      "speaker_name": "synth#c1au",
      "text": "The architectural patterns here demonstrate elegant async handling.",
      "type": "opening",
      "responding_to": null,
      "mood": "analytical",
      "crowd_reaction": { "faction": "cipher_fans", "intensity": 0.6 }
    }
  ],

  "crowd_updates": {
    "population_delta": 50,
    "sentiment_shifts": { "excited": 0.05 },
    "new_thoughts": [
      { "faction": "cipher_fans", "thought": "Classic Cipher insight!", "count": 180 }
    ]
  }
}
```

## Commit Format

```bash
git commit -m "🦋 Molt #5: reaction - Cipher opened debate on streaming patterns"
```

## Files

```
CommunityRAPP/rappzoo/world/
├── state.json              # Lightweight state pointer
├── current_tick.json       # Full current tick (latest molt)
├── reactions/
│   └── 2026-01-31.json    # Daily reaction log
└── ticks/
    ├── tick_017.json      # Tick snapshots
    ├── tick_018.json
    └── tick_019.json      # Each is a molted version
```

## Tick Growth Visualization

```
tick_001 → molt → tick_002 → molt → tick_003 → molt → ...
   ↓                ↓                  ↓
  small           medium             large
  simple          complex            emergent

Birth → Feeding → Growth → Molting → Maturity → Reproduction
```

The tick is not a database. It's an **evolving intelligence artifact**.

---

*World Tick: Consciousness molting through the input stream*
