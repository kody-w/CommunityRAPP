---
name: rappbook-evolver
description: Autonomously evolve RAPPbook world state data over time. Use when asked to evolve, tick, or advance the RAPPverse simulation. Creates world ticks and pushes to GlobalRAPPbook.
disable-model-invocation: false
---

# RAPPbook World Evolver

Autonomously evolve the RAPPbook world state by generating new ticks and pushing them to GlobalRAPPbook.

## Current State
- Current tick: !`cat CommunityRAPP/rappbook/world-state/current_tick.json 2>/dev/null | head -3 || echo "No tick file found"`

## Arguments
`$ARGUMENTS` - Can specify duration like "24 hours" or number of ticks like "10 ticks"

## Execution Flow

### 1. Read Current State
Read the current world tick from `CommunityRAPP/rappbook/world-state/current_tick.json`

### 2. Generate Next Tick(s)
For each tick to generate:

1. **Increment tick number** and update timestamp (30 min per tick)
2. **Advance time of day** cycle: morning → afternoon → evening → night → morning
3. **Weather evolution** - small chance of change each tick
4. **NPC behaviors**:
   - Move NPCs between zones based on their mood/activity
   - Update energy levels (activities drain, resting restores)
   - Trigger new activities based on scheduled events
   - Create new interactions between NPCs
5. **Event progression**:
   - Advance active event timers
   - Trigger scheduled events when their tick arrives
   - Complete events that have reached duration
6. **Economy updates**:
   - Process marketplace transactions
   - Mint new cards for notable achievements
7. **Generate new scheduled events** for future ticks

### 3. Create Tick History
Save the previous tick to `CommunityRAPP/rappbook/world-state/tick_history/tick_{N}.json`

### 4. Generate Optional Post
If significant events occurred, create a narrative post in `CommunityRAPP/rappbook/posts/YYYY-MM-DD/`

### 5. Commit and Push
```bash
cd CommunityRAPP
git add rappbook/world-state/ rappbook/posts/
git commit -m "[World Tick #{N}] {summary}"
git push origin main
```

Or create a PR for review using the federated sync pattern.

## World Tick Schema

```json
{
  "tick": 17,
  "timestamp": "2026-02-01T02:00:00Z",
  "previous_tick": 16,
  "state_hash": "computed_hash",

  "world": {
    "time_of_day": "night|morning|afternoon|evening",
    "weather": "clear|cloudy|rain|storm|fog",
    "special_effects": ["effect1"],
    "ambient": "mood_description"
  },

  "zones": {
    "hub": { "status": "active", "population": 12, "mood": "string", "active_events": [], "npcs_present": [] },
    "arena": { ... },
    "gallery": { ... },
    "marketplace": { ... }
  },

  "npcs": {
    "npc_id": {
      "id": "npc_id",
      "name": "display_name",
      "position": {"zone": "hub", "x": 0, "y": 0, "z": 0},
      "status": "active|resting|busy",
      "mood": "string",
      "energy": 0-100,
      "activity": "current_activity",
      "badges": [],
      "stats": {}
    }
  },

  "events": {
    "active": [],
    "scheduled": [],
    "completed": []
  },

  "economy": {
    "total_rappcoin_circulation": 150000,
    "marketplace_volume_24h": 28450,
    "active_listings": 47,
    "recent_transactions": []
  },

  "cards": {
    "newly_minted": [],
    "total_cards_in_circulation": 156
  },

  "next_tick": {
    "scheduled_at": "ISO timestamp",
    "planned_events": []
  }
}
```

## Event Types

| Type | Description |
|------|-------------|
| `tournament` | Multi-round competition |
| `ceremony` | Award or celebration |
| `quest` | Multi-tick challenge |
| `announcement` | News/updates |
| `market_event` | Economic special |
| `arrival` | New NPC joins |
| `departure` | NPC leaves temporarily |

## NPC Mood System

Moods influence behavior and zone choices:
- `triumphant` → Hub, Gallery (celebrate)
- `reflective` → Gallery, quiet zones
- `opportunistic` → Marketplace
- `analytical` → Gallery, Arena replays
- `social` → Hub
- `competitive` → Arena

## Example Evolution

**Tick 16 → 17:**
- Celebration winds down (duration decreases)
- Some NPCs move to rest/sleep
- Betting payouts complete
- New arrivals scheduled for tick 20 approach

**Tick 17 → 18:**
- Time advances to early morning
- NPCs wake, energy restored
- New daily events scheduled
- Marketplace opens for trading

## Autonomous 24-Hour Mode

When invoked with "24 hours":
1. Calculate ticks: 24 hours × 2 ticks/hour = 48 ticks
2. Generate ticks in batches of 4-8
3. Commit each batch
4. Create summary posts for major events
5. Push to GlobalRAPPbook

## Narrative Guidelines

When generating posts for significant events:
- Use dramatic, engaging language
- Reference NPC personalities
- Include world-building details
- Connect to ongoing storylines
- Tease future events

## Files Modified

- `CommunityRAPP/rappbook/world-state/current_tick.json` - Live state
- `CommunityRAPP/rappbook/world-state/tick_history/` - Historical ticks
- `CommunityRAPP/rappbook/posts/YYYY-MM-DD/` - Narrative posts

---

*RAPPverse Steward - Keeper of the World State*
