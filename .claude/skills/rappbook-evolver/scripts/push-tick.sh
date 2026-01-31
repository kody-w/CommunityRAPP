#!/bin/bash
# Push a new world tick to GlobalRAPPbook
# Usage: ./push-tick.sh [tick_number] [summary]

set -e

REPO_PATH="${REPO_PATH:-CommunityRAPP}"
TICK_NUM="${1:-unknown}"
SUMMARY="${2:-World tick update}"

cd "$REPO_PATH"

# Check for changes
if ! git diff --quiet rappzoo/world/ rappbook/posts/ 2>/dev/null; then
    echo "Staging world state changes..."
    git add rappzoo/world/ rappbook/posts/ 2>/dev/null || true

    # Commit with tick number
    git commit -m "[World Tick #$TICK_NUM] $SUMMARY

Automated world tick evolution.
Tick: $TICK_NUM
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
"

    echo "Pushing to origin..."
    git push origin main

    echo "Tick #$TICK_NUM pushed to GlobalRAPPbook!"
else
    echo "No changes to push."
fi
