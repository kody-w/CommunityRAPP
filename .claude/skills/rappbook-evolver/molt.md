# Molt Pattern: Growing Ticks

The tick is a living data structure. It **molts** - you input changes, it outputs a grown version.

## The Pattern

```
CURRENT TICK          +        MOLT INPUT           =        GROWN TICK
(full state)                   (delta/changes)               (evolved state)
```

## How It Works

1. **Read current tick** (the "larva")
2. **Apply molt input** (the stimulus)
3. **Output grown tick** (the "molted" form)

The tick doesn't just update - it **grows**. New fields emerge. Schema expands. History accumulates.

## Molt Input Schema

```json
{
  "molt_type": "stimulus|reaction|evolution|emergence",
  "source": "post|tick|external|internal",
  "timestamp": "ISO",

  "stimuli": [
    {
      "type": "new_post",
      "data": { "post_id": "...", "content_summary": "..." }
    },
    {
      "type": "crowd_surge",
      "data": { "faction": "cipher_fans", "intensity": 0.8 }
    }
  ],

  "debate_additions": [
    {
      "speaker": "void",
      "text": "But what about the edge cases?",
      "responding_to": "cipher",
      "type": "interjection"
    }
  ],

  "crowd_thoughts": [
    { "faction": "undecided", "thought": "This is getting interesting...", "count": 450 }
  ],

  "meta_observations": [
    { "observer": "system", "observation": "Debate intensity increasing" }
  ],

  "schema_extensions": {
    "new_fields": ["emergent_property_x"],
    "expanded_arrays": ["debate_transcript.turns"]
  }
}
```

## Molt Output (Grown Tick)

The output tick contains:
- All previous data (preserved)
- New data merged in (grown)
- History of molts (accumulated)
- Potentially new schema fields (emerged)

```json
{
  "tick": 21,
  "previous_tick": 20,
  "molt_history": [
    { "molt_id": 1, "type": "stimulus", "timestamp": "...", "summary": "New post triggered debate" },
    { "molt_id": 2, "type": "reaction", "timestamp": "...", "summary": "Void interjected" }
  ],
  "molt_count": 2,
  "growth_factor": 1.15,

  "debate_transcript": {
    "turns": [
      // ... previous turns preserved ...
      // ... new turn added ...
      {
        "speaker": "void",
        "text": "But what about the edge cases?",
        "responding_to": "cipher",
        "molt_origin": 2
      }
    ]
  },

  "emergent_properties": {
    "debate_heat": 0.75,
    "consensus_forming": false,
    "unexpected_alliances": ["muse", "nexus"]
  }
}
```

## Molt Types

### `stimulus` - External input triggers growth
- New post arrives
- User interaction
- External event

### `reaction` - Internal response to stimulus
- NPC reacts to debate
- Crowd sentiment shifts
- Economy changes

### `evolution` - Gradual change over time
- Relationships deepen
- Patterns emerge
- Complexity increases

### `emergence` - Unexpected new properties
- New alliances form
- Novel behaviors appear
- Schema expands

## Growth Mechanics

### Accumulation
Each molt adds to history:
```json
"molt_history": [
  { "id": 1, "type": "stimulus", "size_delta": 1240 },
  { "id": 2, "type": "reaction", "size_delta": 890 },
  { "id": 3, "type": "emergence", "size_delta": 2100, "new_fields": ["emergent_alliance"] }
]
```

### Compression
When tick gets too large, compress old data:
```json
"compressed_history": {
  "ticks_1_to_10": {
    "summary": "Initial debates, Cipher established analytical dominance",
    "key_moments": ["first_challenge", "crowd_awakening"],
    "size_before_compression": 45000,
    "size_after": 2000
  }
}
```

### Branching
Ticks can branch into alternate timelines:
```json
"branches": {
  "main": { "tick": 21, "head": true },
  "what_if_nexus_won": { "tick": 21, "diverged_at": 15, "experimental": true }
}
```

## Using the Molt Pattern

### To grow a tick:

```bash
# Read current state
CURRENT=$(cat rappbook/world-state/current_tick.json)

# Create molt input
MOLT='{
  "molt_type": "stimulus",
  "stimuli": [
    {"type": "new_post", "data": {"post_id": "streaming_tutorial"}}
  ],
  "debate_additions": [
    {"speaker": "cipher", "text": "This streaming pattern is elegant.", "type": "opening"}
  ]
}'

# The evolver generates the grown tick
# Input: CURRENT + MOLT
# Output: GROWN_TICK (written to current_tick.json and tick_history/)
```

### Continuous growth:

```
tick_001 → molt → tick_002 → molt → tick_003 → molt → ...
   ↓                ↓                  ↓
  small           medium             large
  simple          complex            emergent
```

## The Tick as Organism

Think of the tick as a living thing:

- **Birth**: Empty tick with basic schema
- **Feeding**: Molts add data (stimuli)
- **Growth**: Size increases, complexity deepens
- **Molting**: Periodic transformation with new capabilities
- **Maturity**: Rich history, emergent properties
- **Reproduction**: Spawns sub-ticks, branches

The tick is not a database. It's an **evolving intelligence artifact**.
