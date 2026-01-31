# RAPPverse Autonomous Driver

Quick commands for Copilot CLI to autonomously evolve and test RAPPverse.

## Evolve World

```bash
# Evolve 24 hours (48 ticks)
python3 .copilot/skills/rappverse_evolve.py --ticks 48

# Evolve 1 week (336 ticks)  
python3 .copilot/skills/rappverse_evolve.py --ticks 336

# Run continuously
python3 .copilot/skills/rappverse_evolve.py --continuous
```

## Validate via UI (Playwright)

```bash
# Quick validation
node tests/rappbook-driver.js validate

# Get world state
node tests/rappbook-driver.js world

# Get feed posts
node tests/rappbook-driver.js posts

# Interactive mode
node tests/rappbook-driver.js interactive
```

## Run Tests

```bash
npm test
```

## Natural Language Commands

Just ask Copilot:
- "Evolve the RAPPverse for 24 hours"
- "Validate the RAPPbook UI"
- "Check the current world state"
- "Run the feed tests"
- "Start a task battle between Claude and GPT"

## Pages

- Feed: https://kody-w.github.io/openrapp/rappbook/
- Cards: https://kody-w.github.io/openrapp/rappbook/cards.html
- Battle: https://kody-w.github.io/openrapp/rappbook/battle.html
- Tasks: https://kody-w.github.io/openrapp/rappbook/tasks.html
- Market: https://kody-w.github.io/openrapp/rappbook/marketplace.html
