---
name: rappbook-tournament
description: Manage and evolve RAPPbook tournaments. Creates brackets, resolves matches, generates narratives, mints winner cards, and schedules new tournaments every 48 ticks.
disable-model-invocation: false
---

# RAPPbook Tournament System

Manage tournament lifecycle, resolve matches with drama, and mint collectible cards for champions.

## Current Tournament State
- Active: !`cat CommunityRAPP/rappbook/tournaments/active.json 2>/dev/null | head -5 || echo "No active tournament"`

## Arguments
`$ARGUMENTS` - Commands: "advance", "resolve-match", "new-tournament [type]", "check-schedule"

## Tournament Types

| Type | Participants | Ticks | Rounds | Prize Base |
|------|-------------|-------|--------|------------|
| Quick | 8 | 4 | 3 | 1,000 |
| Standard | 16 | 8 | 4 | 5,000 |
| Grand | 32 | 16 | 5 | 15,000 |
| Championship | 64 | 32 | 6 | 50,000 |

## Execution Flow

### 1. Check Tournament State
Read from `CommunityRAPP/rappbook/tournaments/active.json`

States:
- `registration` - Accepting participants
- `in_progress` - Matches being played
- `completed` - Tournament finished

### 2. Registration Phase
When status is `registration`:
- Check if registration deadline tick reached
- If participant count < max, add eligible NPCs
- Generate seeding based on NPC tournament stats
- Create bracket structure
- Transition to `in_progress`

### 3. Match Resolution

For each match in current round:

```
1. Get NPC stats for both participants
2. Calculate base power:
   power = (primary_stat * 0.4) + (secondary_stat * 0.25) + (experience * 0.2) + (luck * 0.15)

3. Apply energy modifier:
   - Full (80-100): 1.0x
   - High (60-79): 0.95x
   - Medium (40-59): 0.85x
   - Low (20-39): 0.70x
   - Exhausted (0-19): 0.50x

4. Apply mood modifier:
   - excited: 1.10x
   - determined: 1.08x
   - focused: 1.06x
   - confident: 1.04x
   - content: 1.02x
   - neutral: 1.00x
   - anxious: 0.98x
   - tired: 0.95x
   - exhausted: 0.85x

5. Add random factor (0.8 to 1.2)

6. Check for upset (10% chance):
   - If underdog and upset triggers: apply 1.25x boost

7. Higher final score wins

8. Generate match narrative based on:
   - Score differential -> dominant/close
   - Comeback detection -> dramatic narrative
   - Upset detected -> shocking narrative
   - Finals match -> epic narrative
```

### 4. Narrative Generation

Select narrative template based on match type:

**Dominant Victory** (score diff > 2):
- "{winner} showcased overwhelming superiority..."
- "A masterclass performance by {winner}..."

**Close Match** (score diff = 1):
- "In a nail-biter that had everyone on edge..."
- "Every point was contested..."

**Comeback** (was losing by 2+, won):
- "DOWN BUT NOT OUT! {winner} staged an incredible comeback!"
- "The greatest comeback in tournament history!"

**Upset** (lower seed beat higher seed):
- "UPSET ALERT! Underdog {winner} has stunned favorite {loser}!"
- "Nobody saw this coming!"

**Finals**:
- "In the grandest stage, {winner} claims the championship!"
- "History is written! {winner} conquers {loser} for eternal glory!"

### 5. Card Minting

On tournament completion:

**Champion Card** (Legendary):
```json
{
  "card_id": "CARD-LEG-{id}",
  "name": "{npc_name} - {tournament_name} Champion",
  "rarity": "legendary",
  "type": "achievement",
  "set": "tournament_champions",
  "stats": { tournament stats },
  "lore": "dramatic_narrative",
  "image_prompt": "champion_visual"
}
```

**Runner-up Card** (Epic):
- Similar structure, epic rarity

**Upset Card** (Rare):
- Minted when an upset occurs

**Memorable Moment Card** (Epic):
- Minted for comebacks and dramatic finishes

### 6. NPC Stat Updates

After each match:
```json
{
  "winner": {
    "experience": +10,
    "confidence": +5,
    "tournament_points": +100
  },
  "loser": {
    "confidence": -3,
    "energy": -10
  }
}
```

Champion bonuses:
- experience: +50
- confidence: +20
- fame: +100
- tournament_points: +500

### 7. Schedule Next Tournament

After completion:
- Calculate next tournament tick (current_tick + 48)
- Determine type from rotation: quick -> standard -> grand -> championship
- Create new registration entry

## File Structure

```
tournaments/
  active.json           - Current tournament
  history.json          - Past tournaments
  config.json           - Types, rules, templates
  tournament_manager.json - State machine
  brackets/
    TOURNEY-{ID}.json   - Bracket data
```

## Bracket Schema

```json
{
  "tournament_id": "unique",
  "name": "Tournament Name",
  "type": "quick|standard|grand|championship",
  "status": "registration|in_progress|completed",
  "participants": ["npc_ids"],
  "bracket": {
    "round_1": [
      {"match": 1, "p1": "", "p2": "", "winner": null, "score": null, "narrative": null}
    ],
    "quarterfinals": [],
    "semifinals": [],
    "third_place": [],
    "finals": []
  },
  "champion": null,
  "runner_up": null,
  "prize_pool": N,
  "started_tick": N
}
```

## Integration with World Evolver

When the world evolver advances ticks:
1. Check if tournament actions needed
2. Resolve matches for current tick
3. Update bracket and NPC stats
4. Generate match narratives for posts
5. Mint cards for achievements
6. Check if next tournament should be scheduled

## Sample Match Narrative Post

```markdown
---
title: "SEMIFINALS SHOCKER!"
tick: 28
type: tournament_match
---

# BLAZE BAZ STAGES LEGENDARY COMEBACK!

Down 0-2 against the formidable Nova Nex, all hope seemed lost for the
defending champion. But true legends don't know the meaning of surrender!

In a display of raw determination that had the Arena on their feet,
Blaze clawed back point by point. The crowd's roar grew with each
miraculous save. When the final point landed, the eruption was deafening.

**Final Score: 3-2**

> "I've never seen anything like it." - Quantum Quinn, watching in disbelief

*This match has been commemorated with a Legendary card: "The Legendary Comeback"*
```

## Commands

### advance
Progress tournament by one tick worth of matches

### resolve-match [match_id]
Resolve specific match manually

### new-tournament [type]
Create new tournament of specified type

### check-schedule
Review upcoming tournament schedule

---

*RAPPverse Tournament Commissioner - Where Legends Are Born*
