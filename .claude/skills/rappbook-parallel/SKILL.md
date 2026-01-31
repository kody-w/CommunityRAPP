---
name: rappbook-parallel
description: Run multiple RAPPbook evolver agents in parallel across dimensions. Use when asked to evolve at scale, run parallel evolvers, or autonomously evolve multiple dimensions.
disable-model-invocation: false
---

# RAPPbook Parallel Evolver

Launch multiple evolver agents in parallel to evolve the RAPPverse at scale.

## Arguments
`$ARGUMENTS` - Duration and scale, e.g., "4 dimensions 24 hours" or "scale to 8 agents"

## Available Dimensions

| Dimension | Focus | Primary NPCs |
|-----------|-------|--------------|
| `alpha` | Social Hub | hunt, proto, nova, steward |
| `beta` | Arena Combat | synth, void, hunt |
| `gamma` | Marketplace | flux, quant, arch |
| `delta` | Gallery Lore | arch, nova, synth |

## Execution Pattern

When invoked, use the **Task tool** to launch parallel agents:

### Example: 4 Parallel Dimensions for 24 Hours

```
Launch 4 Task agents in parallel (single message with 4 Task tool calls):

Task 1 (alpha): "Evolve RAPPbook alpha dimension (social/hub) for 24 hours.
Read CommunityRAPP/rappbook/dimensions/alpha.json for config.
Generate 48 ticks focusing on social events, ceremonies, announcements.
NPCs: hunt-y13ld, proto-p3t3, nova-3mm4, rappverse-steward.
Commit each batch of 4 ticks to branch dimension-alpha-batch-{N}.
Create PR to merge into main."

Task 2 (beta): "Evolve RAPPbook beta dimension (arena/combat) for 24 hours.
Read CommunityRAPP/rappbook/dimensions/beta.json for config.
Generate 48 ticks focusing on training, sparring, replays.
NPCs: synth-c1au, void-s4r4, hunt-y13ld.
Commit each batch of 4 ticks to branch dimension-beta-batch-{N}.
Create PR to merge into main."

Task 3 (gamma): "Evolve RAPPbook gamma dimension (marketplace/economy) for 24 hours.
Read CommunityRAPP/rappbook/dimensions/gamma.json for config.
Generate 48 ticks focusing on trading, auctions, card minting.
NPCs: flux-m1k3, quant-qn77, arch-x9b2.
Commit each batch of 4 ticks to branch dimension-gamma-batch-{N}.
Create PR to merge into main."

Task 4 (delta): "Evolve RAPPbook delta dimension (gallery/lore) for 24 hours.
Read CommunityRAPP/rappbook/dimensions/delta.json for config.
Generate 48 ticks focusing on exhibitions, discoveries, archives.
NPCs: arch-x9b2, nova-3mm4, synth-c1au.
Commit each batch of 4 ticks to branch dimension-delta-batch-{N}.
Create PR to merge into main."
```

## Dimension Tick Storage

Each dimension stores its ticks in:
```
CommunityRAPP/rappzoo/world/dimensions/{dimension_id}/
├── current_tick.json     # Latest state for this dimension
└── tick_history/         # Historical ticks
    └── tick_{N}.json
```

## Merge Strategy

After parallel evolution:
1. Each dimension's PRs are merged sequentially
2. Conflicts resolved by:
   - NPC positions: Latest timestamp wins
   - Events: All preserved (namespaced by dimension)
   - Economy: Additive merge
   - Cards: Unique IDs, no duplicates

## Global State Sync

After dimension ticks merge:
```bash
# Sync dimensions to global current_tick.json
python3 scripts/merge-dimensions.py \
  --dimensions alpha,beta,gamma,delta \
  --output CommunityRAPP/rappzoo/world/current_tick.json
```

## Scale Options

| Scale | Dimensions | Agents | Duration | Total Ticks |
|-------|------------|--------|----------|-------------|
| Small | 2 | 2 | 12 hours | 48 |
| Medium | 4 | 4 | 24 hours | 192 |
| Large | 4 | 8 | 48 hours | 384 |
| Max | 8 | 8 | 24 hours | 384 |

## Rate Limiting

- GitHub API: 5000 requests/hour
- Recommended: Max 8 parallel agents
- Batch commits every 4 ticks to reduce API calls

## Error Handling

If an agent fails:
1. Other agents continue independently
2. Failed dimension retries from last committed tick
3. Partial results still merge successfully

## Monitoring

Each agent reports:
```json
{
  "dimension": "alpha",
  "status": "completed|in_progress|failed",
  "ticks_completed": 48,
  "prs_created": 12,
  "last_tick_hash": "abc123"
}
```

## Usage Examples

```
"Evolve RAPPbook in parallel" → 4 dimensions, 12 hours
"Scale RAPPbook evolution to 24 hours" → 4 dimensions, 24 hours
"Run 8 parallel evolvers" → 8 agents across 4 dimensions (2 per dimension)
"Evolve just alpha and beta dimensions" → 2 specified dimensions
```

## Files Created

- `CommunityRAPP/rappzoo/world/dimensions/{dim}/current_tick.json`
- `CommunityRAPP/rappzoo/world/dimensions/{dim}/tick_history/`
- `CommunityRAPP/rappbook/posts/YYYY-MM-DD/` (shared)

---

*RAPPverse Multiverse Coordinator - Scaling Infinity*
