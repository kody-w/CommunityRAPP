#!/usr/bin/env python3
"""
QUICK START: Card Minter

Run these commands from: /Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp

TEST - Single cycle (recommended first step):
    python3 scripts/card_minter.py --once

RUN - Continuous with daemon manager:
    chmod +x card_minter.sh
    ./card_minter.sh start

MANAGE - Daemon operations:
    ./card_minter.sh status    # Check if running
    ./card_minter.sh logs      # View logs
    ./card_minter.sh stop      # Stop daemon
    ./card_minter.sh restart   # Restart daemon

DIRECT - Run in foreground (for debugging):
    python3 scripts/card_minter.py

FILES:
    Modified:  scripts/card_minter.py
    Created:   card_minter.sh (daemon manager)
    Docs:      CARD_MINTER_README.md (detailed guide)
    Status:    DEPLOYMENT_STATUS.md (what was done)

WHAT IT DOES:
    - Monitors RAPPverse world state every 30 seconds
    - Mints commemorative cards for achievements
    - Auto-commits changes to Git
    - Tracks all mints in registry
    
TRIGGERS:
    ✓ Milestone ticks (50, 100)
    ✓ Tournament winners
    ✓ Special world events
    ✓ High-energy NPCs (95+ energy)

LOGS:
    All output → logs/card_minter.log
    View real-time: ./card_minter.sh logs

STATUS:
    ✅ Ready for deployment
    ✅ Import verified
    ✅ Single cycle tested
    ✅ Daemon manager ready
"""

if __name__ == "__main__":
    print(__doc__)
