#!/bin/bash
# Quick setup script to create the auctions directory and JSON file

DIR="/Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp/CommunityRAPP/rappbook/auctions"
mkdir -p "$DIR"
echo "✓ Created directory: $DIR"

# Run the Python setup script
python3 "/Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp/setup_auctions.py"
