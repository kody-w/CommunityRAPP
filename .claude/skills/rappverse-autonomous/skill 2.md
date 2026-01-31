---
name: rappverse-autonomous
description: Launch full autonomous RAPPverse evolution for 24 hours. Spawns 50+ parallel agents across all systems. Use when asked to "evolve rappverse", "run autonomous evolution", or "start the rappverse". Runs until user says stop.
disable-model-invocation: false
---

# RAPPverse Autonomous Evolution System

Launch the complete autonomous RAPPverse simulation with 50+ parallel agents.

## Arguments
`$ARGUMENTS` - Duration like "24 hours" or "until stop". Default: 24 hours continuous.

## Quick Start

When invoked, immediately launch ALL agent categories in parallel using the Task tool with `run_in_background: true`.

## Agent Fleet Architecture

### Tier 1: Core Evolution Waves (12 agents)
Launch evolution waves covering extended timeline:

```
Waves 1-4: Ticks 19-210 (Days 1-5)
Waves 5-8: Ticks 211-402 (Days 6-10)
Waves 9-12: Ticks 403-594 (Days 11-15)
```

Each wave agent prompt:
```
AUTONOMOUS RAPPBOOK EVOLUTION - WAVE {N}
Base: /Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp/CommunityRAPP/rappbook/world-state/
Wait for tick {prev} to exist, then evolve ticks {start}-{end}.
Update current_tick.json, save to tick_history/.
Commit each batch of 4 ticks.
Push to origin main.
Work autonomously.
```

### Tier 2: Dimension Evolvers (8 agents)
4 dimensions x 2 wave coverage each:

| Dimension | Focus | Agents |
|-----------|-------|--------|
| Alpha | Social/Hub | 2 |
| Beta | Arena/Combat | 2 |
| Gamma | Marketplace | 2 |
| Delta | Gallery/Lore | 2 |

### Tier 3: World Systems (30+ agents)
Launch ALL support systems in parallel:

| System | Purpose |
|--------|---------|
| Narrative Generator | Story posts |
| NPC Relationships | Friendship tracking |
| Card Minting | Achievement cards |
| Weather System | Dynamic weather |
| Quest System | NPC quests |
| Event Scheduler | Future events |
| NPC Spawner | New arrivals |
| Dimension Sync | Cross-dimension |
| Economy Analytics | Market tracking |
| Lore Generator | World lore |
| Achievement System | Achievements |
| Tournament System | Brackets |
| Social Feed | NPC posts |
| Zone Manager | Zone dynamics |
| Daily Digest | Summaries |
| Reputation System | NPC rep |
| Storyline Manager | Story arcs |
| Mystery Events | Mysteries |
| Seasonal Events | Festivals |
| NPC Dialogue | Conversations |
| Auction House | Auctions |
| Training System | Skill growth |
| Guild System | Factions |
| Faction Wars | Conflicts |
| Crafting System | Item creation |
| Companion System | Pets |
| Entertainment | Performances |
| Dream System | Visions |
| Leaderboards | Rankings |
| News System | Journalism |
| Housing | Properties |
| Festival System | Holidays |
| Mentorship | Teaching |
| Secret Societies | Hidden groups |
| Emotion System | Mood tracking |
| Collection System | Collectibles |
| Legacy System | Inheritance |
| Diplomacy | Faction relations |
| Bounty System | Contracts |
| Random Events | Unpredictability |
| Time Capsules | Memories |

## Execution Pattern

Launch in a SINGLE message with multiple Task tool calls:

```javascript
// Launch all agents in parallel
Task(wave1, background=true)
Task(wave2, background=true)
Task(wave3, background=true)
// ... (all 12 waves)
Task(alpha_dim, background=true)
Task(beta_dim, background=true)
// ... (all dimensions)
Task(narrative, background=true)
Task(relationships, background=true)
// ... (all 30+ systems)
```

## System Agent Template

Each system agent follows this pattern:

```
RAPPBOOK {SYSTEM_NAME} SYSTEM

Path: /Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp/CommunityRAPP/rappbook/

1. Create {system}/ folder with required JSON files
2. Monitor world-state/current_tick.json
3. Generate content based on world state
4. Create narrative posts for significant events
5. Commit changes with "[{System}] {description}"
6. Push to origin main
7. Work continuously until stopped
```

## Monitoring

Check agent status:
```bash
# View all running agents
ls /private/tmp/claude-*/tasks/*.output | xargs tail -1

# Check specific agent
tail -f /private/tmp/claude-*/tasks/{agent_id}.output
```

## Stopping Evolution

When user says "stop":
1. All background agents will complete their current tick
2. Final state is committed
3. Summary of evolution is provided

## File Structure Created

```
CommunityRAPP/rappbook/
├── world-state/
│   ├── current_tick.json
│   ├── tick_history/
│   └── dimensions/{alpha,beta,gamma,delta,epsilon,zeta}/
├── achievements/
├── auctions/
├── bounties/
├── capsules/
├── cards/
├── collections/
├── companions/
├── crafting/
├── dialogue/
├── digests/
├── diplomacy/
├── dreams/
├── economy/
├── emotions/
├── entertainment/
├── events/
├── feed/
├── festivals/
├── guilds/
├── housing/
├── leaderboards/
├── legacy/
├── lore/
├── mentorship/
├── mysteries/
├── news/
├── npcs/
├── posts/
├── prophecy/
├── quests/
├── random/
├── relationships/
├── reputation/
├── seasons/
├── secrets/
├── storylines/
├── sync/
├── tavern/
├── tournaments/
├── training/
├── travel/
├── wars/
└── weather/
```

## Usage

```
/rappverse-autonomous 24 hours  -> Full 24-hour evolution
/rappverse-autonomous           -> Default 24 hours
/rappverse-autonomous until stop -> Run indefinitely
```

## On Invocation

IMMEDIATELY launch 50+ Task agents in parallel using a single message with multiple Task tool calls. All agents run in background (`run_in_background: true`).

Do NOT wait for confirmation. Start evolution immediately.

---

*RAPPverse Autonomous Steward - The World That Runs Itself*
