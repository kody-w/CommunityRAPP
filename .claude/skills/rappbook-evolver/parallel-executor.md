# Parallel RAPPverse Evolution

Execute multiple evolver agents in parallel using dimension sharding.

## Parallel Execution Pattern

### Single Dimension (Sequential)
```
/rappbook-evolver 24 hours
```

### Multi-Dimension (Parallel)
Launch multiple agents, each handling a dimension:

```bash
# Each dimension evolves independently, then merges to GlobalRAPPbook
# Dimensions are identified by unique IDs in their tick data
```

## Dimension Sharding

Each parallel agent gets assigned a dimension shard:

| Dimension | Focus | NPCs | Events |
|-----------|-------|------|--------|
| `alpha` | Hub & Social | hunt, proto, steward | Ceremonies, Announcements |
| `beta` | Arena & Combat | synth, void, nova | Training, Replays |
| `gamma` | Market & Economy | flux, quant, arch | Trading, Minting |
| `delta` | Gallery & Lore | All visitors | Exhibitions, History |

## Parallel Agent Invocation

To run in parallel, use Claude's Task tool with multiple instances:

```
User: "Evolve RAPPbook in parallel across 4 dimensions for 24 hours"

Claude: [Creates 4 Task tool calls in parallel]
- Task 1: "Evolve alpha dimension - social/ceremonies"
- Task 2: "Evolve beta dimension - arena/combat"
- Task 3: "Evolve gamma dimension - marketplace/economy"
- Task 4: "Evolve delta dimension - gallery/lore"
```

## Merge Strategy

Dimensions merge deterministically:
1. Each dimension generates ticks with unique `dimension_id` prefix
2. Events are namespaced: `{dimension}_{event_id}`
3. NPC positions merge by latest timestamp
4. Economy merges additively
5. Cards merge by unique ID

## Tick ID Format

```
{dimension}_{tick_number}_{timestamp_hash}
```

Example: `alpha_017_a1b2c3d4`

## Conflict Resolution

When dimensions produce conflicting data:
1. **NPC Position**: Latest timestamp wins
2. **Events**: All events preserved (namespaced)
3. **Economy**: Sum transactions, take max circulation
4. **Cards**: Merge by unique ID, duplicates = first wins

## Parallel Commit Pattern

Each dimension commits to its own branch:
```bash
git checkout -b dimension-{name}-tick-{N}
git add rappzoo/world/dimensions/{name}/
git commit -m "[{name}] Tick #{N}"
git push origin dimension-{name}-tick-{N}
gh pr create --title "[{name}] Tick #{N}" --body "Dimension sync"
```

## Orchestrator Pattern

For 24-hour autonomous evolution:

```python
dimensions = ['alpha', 'beta', 'gamma', 'delta']
duration_hours = 24
ticks_per_hour = 2
total_ticks = duration_hours * ticks_per_hour  # 48 ticks

# Each dimension handles 48 ticks
# Merge happens every 4 ticks (2 hours)
merge_interval = 4

for batch in range(total_ticks // merge_interval):
    # Parallel: Each dimension evolves 4 ticks
    parallel_evolve(dimensions, ticks=merge_interval)

    # Sequential: Merge all dimensions
    merge_dimensions(dimensions)

    # Push merged state
    push_to_global()
```

## Dimension Config Files

Create dimension config in `CommunityRAPP/rappbook/dimensions/`:

```json
{
  "dimension_id": "alpha",
  "name": "Alpha Dimension",
  "focus": "social",
  "npcs": ["hunt-y13ld", "proto-p3t3", "rappverse-steward"],
  "zones": ["hub"],
  "event_types": ["ceremony", "announcement", "social"]
}
```

## Usage Examples

### 4 Parallel Agents
```
"Run 4 RAPPbook evolvers in parallel for 12 hours each"
```

### Dimension-Specific
```
"Evolve the marketplace dimension (gamma) for 24 hours"
```

### Full Scale
```
"Autonomously evolve RAPPbook at scale - 4 dimensions, 24 hours, merge every 2 hours"
```

## Output

Each parallel agent returns:
```json
{
  "dimension": "alpha",
  "ticks_generated": 48,
  "events_created": 12,
  "npcs_moved": 156,
  "cards_minted": 3,
  "commits": ["abc123", "def456", ...],
  "prs_created": 12
}
```

## Scaling Beyond 4

For larger scale:
1. Create more dimension configs
2. Shard NPCs across dimensions
3. Use time-based sharding (each agent handles 6 hours)
4. Geographic sharding (each zone = dimension)

Maximum parallel: Limited by GitHub API rate limits (5000/hr) and merge conflicts.

Recommended: 4-8 parallel dimensions for optimal throughput.
