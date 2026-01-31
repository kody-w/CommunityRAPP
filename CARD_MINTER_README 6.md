# Card Minter Implementation Summary

## Changes Made

### 1. Modified `scripts/card_minter.py`
- Added `run_once` parameter to `main()` function
- Script now accepts `--once` flag for single cycle execution
- Default behavior remains continuous loop (original functionality)

**Usage:**
```bash
# Run single cycle (for testing)
python3 scripts/card_minter.py --once

# Run continuously (default)
python3 scripts/card_minter.py
```

### 2. Created `card_minter.sh` - Daemon Manager
A complete bash wrapper for managing the card minter as a daemon service.

**Features:**
- Start/stop/restart the daemon
- Check status and view logs
- Run single test cycles
- Automatic PID file management
- Graceful shutdown with force kill fallback
- Log file management

**Usage:**
```bash
# Start continuous daemon
./card_minter.sh start

# Stop daemon
./card_minter.sh stop

# Restart daemon
./card_minter.sh restart

# Check status
./card_minter.sh status

# Run single test cycle
./card_minter.sh test

# View logs in real-time
./card_minter.sh logs
```

### 3. Created `scripts/card_minter_single.py`
A standalone version with single-cycle code only (for reference/testing).

## How to Use

### Step 1: Test Single Cycle
```bash
cd /Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp
python3 scripts/card_minter.py --once
```

This will:
- Load current world state from `CommunityRAPP/rappbook/world-state/current_tick.json`
- Check for minting opportunities
- Process one cycle and exit
- Display any cards minted

### Step 2: Run Continuous Daemon
```bash
# Make script executable
chmod +x card_minter.sh

# Start the daemon
./card_minter.sh start

# Check status
./card_minter.sh status

# View logs
./card_minter.sh logs

# Stop when done
./card_minter.sh stop
```

## File Locations

- **Main script:** `scripts/card_minter.py`
- **Daemon manager:** `card_minter.sh`
- **Logs:** `logs/card_minter.log`
- **PID file:** `logs/card_minter.pid`

## Minting Triggers

The card minter monitors for:
1. **Milestone ticks** - Cards at 50-tick and 100-tick intervals
2. **Tournament events** - Champion cards when tournaments complete
3. **Special events** - Discovery, mystery, celebration, performance events
4. **High-energy NPCs** - NPCs with 95+ energy levels

## Data Structures Updated

When cards are minted, the following files are updated:
- `CommunityRAPP/rappbook/cards/cards_registry.json` - Card metadata and counts
- `CommunityRAPP/rappbook/cards/catalog.json` - Card catalog with rarity distribution
- `CommunityRAPP/rappbook/cards/mint_history.json` - Complete mint audit log
- `CommunityRAPP/rappbook/world-state/current_tick.json` - World state updates

## Git Integration

Each minting cycle automatically:
- Commits changes with descriptive message
- Pushes to origin/main branch
- Includes card names and count in commit message

Example commit: `[Cards] Minted 3 cards: Legendary Card, Epic Card +1 more`

## Next Steps

1. **Test**: Run `python3 scripts/card_minter.py --once` to verify it works
2. **Deploy**: Use `./card_minter.sh start` to run as daemon
3. **Monitor**: Use `./card_minter.sh logs` to watch for issues
4. **Manage**: Use `./card_minter.sh {stop|restart}` to manage the daemon

---

**Status**: ✅ Ready for deployment
**Last Updated**: 2024
