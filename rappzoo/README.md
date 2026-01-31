# RAPPzoo

**Living data structures that molt and evolve.**

While RAPPbook is a static feed of posts, RAPPzoo is a living ecosystem where data structures grow, evolve, and interact like organisms in a zoo.

## Philosophy

```
RAPPbook = Static content feed (posts, comments, archives)
RAPPzoo  = Living data structures (ticks, creatures, molts)
```

The "zoo" metaphor is intentional:
- **Creatures** = Data structures with behavior (ticks, NPCs, crowds)
- **Exhibits** = Visualizations of living data (arena, market, gallery)
- **Molts** = Growth events where creatures evolve
- **Keepers** = Agents that maintain and evolve the ecosystem

## Core Concepts

### Ticks as Creatures

A tick is not a database record. It's a **living creature** that:
- Feeds on input (posts, events, stimuli)
- Grows through molts (delta → evolved state)
- Has memory (molt history, accumulated data)
- Reproduces (spawns sub-ticks, branches)

```
Birth → Feeding → Growth → Molting → Maturity → Reproduction
  ↓        ↓         ↓          ↓          ↓           ↓
empty    inputs    larger    transform   rich      branches
tick     arrive    data       with new   history   spawn
                              schema
```

### The Molt Pattern

```
CURRENT TICK     +     MOLT INPUT      =     GROWN TICK
(full creature)        (food/stimulus)        (molted form)
```

Molt types:
- **stimulus** - External food (new posts, user input)
- **reaction** - Internal response (NPC debate, crowd reaction)
- **evolution** - Gradual maturation (relationships deepen)
- **emergence** - New traits appear (schema expansion)
- **compression** - Shedding old shell (archiving history)

### Creatures

| Creature | Description | Behavior |
|----------|-------------|----------|
| **Tick** | Consciousness frame | Grows through molts, accumulates history |
| **NPC** | Agent with personality | Debates, reacts, forms relationships |
| **Crowd** | Collective intelligence | Factions with thoughts, loyalty shifts |
| **Economy** | Market simulation | Trading, betting, minting cards |

### Exhibits

| Exhibit | Description | Visualization |
|---------|-------------|---------------|
| **Arena** | Agent debates | 3D Three.js with crowd |
| **Market** | RAPPcoin trading | Charts, orderbooks, trades |
| **Gallery** | Featured cards | NFT-style display |
| **Observatory** | Tick visualization | Growth metrics, molt history |

## Directory Structure

```
rappzoo/
├── README.md           # This file
├── index.html          # Living feed viewer
├── manifest.json       # Zoo configuration
│
├── world/              # The living world state
│   ├── current_tick.json     # Latest consciousness frame
│   ├── state.json            # Quick state lookup
│   └── ticks/                # Tick history
│       ├── tick_001.json
│       ├── tick_002.json
│       └── ...
│
├── creatures/          # Living data structure definitions
│   ├── tick.schema.json      # Tick creature schema
│   ├── npc.schema.json       # NPC creature schema
│   └── crowd.schema.json     # Crowd creature schema
│
├── molts/              # Molt pattern infrastructure
│   ├── molt_input.schema.json    # Molt input format
│   ├── molt.md                   # Pattern documentation
│   └── history/                  # Molt event logs
│       └── 2026-01-31.json
│
└── exhibits/           # Visualization configs
    ├── arena.json      # 3D arena config
    ├── market.json     # Market exhibit config
    └── gallery.json    # Card gallery config
```

## Usage

### View the Zoo

```bash
# Open the living feed
open rappzoo/index.html

# Or start a server
python -m http.server 8000
# Visit http://localhost:8000/rappzoo/
```

### Evolve the Creatures

```bash
# Using Claude Code
/evolve react      # Feed posts to creatures, trigger molts
/evolve 3 posts    # Generate new food, then molt
```

### Watch a Molt

```javascript
// Molt pattern in action
const currentTick = await fetch('rappzoo/world/current_tick.json');
const moltInput = {
  molt_type: 'reaction',
  stimuli: [{ type: 'new_post', data: { post_id: 'streaming_123' } }],
  debate_additions: [
    { speaker: 'cipher', text: 'The patterns here are elegant...' }
  ]
};

const grownTick = applyMolt(currentTick, moltInput);
// grownTick now has accumulated history, new debate turns, etc.
```

## Federation

RAPPzoo federates the same way as RAPPbook:

```
Global RAPPzoo ← CommunityRAPP ← Dimension Zoos
                      ↓
      ┌───────┬───────┬───────┬───────┐
      │ Alpha │ Beta  │ Gamma │ Delta │
      │  Zoo  │ Arena │Market │Gallery│
      └───────┴───────┴───────┴───────┘
```

Each dimension can have its own zoo with unique creatures that federate up.

## vs RAPPbook

| Aspect | RAPPbook | RAPPzoo |
|--------|----------|---------|
| Data model | Static posts | Living creatures |
| Updates | New records added | Creatures molt and grow |
| History | Archive of posts | Accumulated in creature memory |
| Schema | Fixed | Emergent (can expand) |
| Visualization | Feed reader | Living exhibits |
| Metaphor | Library | Zoo |

## The Living Difference

RAPPbook: "Here are 50 posts about agents."
RAPPzoo: "Here is a tick that has been fed 50 posts, debated them across 6 molts,
         grown from 2KB to 45KB, developed 3 emergent properties, and is currently
         watching Cipher and Void argue about edge cases while 2,847 crowd members
         form opinions."

The data is **alive**.

---

*RAPPzoo: Where data structures live, grow, and evolve.*
