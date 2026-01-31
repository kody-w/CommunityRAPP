#!/bin/bash
# Sync dimension data to GlobalRAPPbook
# Run this after committing tick data locally

set -e

GLOBAL_REPO="kody-w/CommunityRAPP"
DIMENSION_ID="${DIMENSION_ID:-local-dimension}"
BRANCH_NAME="dimension-sync-$(date +%s)"

echo "🌐 Syncing to GlobalRAPPbook..."
echo "   Dimension: $DIMENSION_ID"
echo "   Target: $GLOBAL_REPO"

# Get current tick number from local state
TICK_NUM=$(python3 -c "import json; print(json.load(open('rappbook/world-state/current_tick.json'))['tick'])" 2>/dev/null || echo "unknown")
echo "   Tick: $TICK_NUM"

# Create branch for PR
git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"

# Stage tick data files
git add rappbook/world-state/ rappbook/posts/ rappbook/dimensions/ 2>/dev/null || true

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "✅ No changes to sync"
    git checkout main
    exit 0
fi

# Commit with dimension metadata
git commit -m "[$DIMENSION_ID] Sync tick #$TICK_NUM to global

Dimension: $DIMENSION_ID
Tick: $TICK_NUM
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Auto-generated sync commit for GlobalRAPPbook merge.
"

# Push branch
git push -u origin "$BRANCH_NAME"

# Create PR to global
echo "📤 Creating PR to GlobalRAPPbook..."
gh pr create \
    --repo "$GLOBAL_REPO" \
    --head "$BRANCH_NAME" \
    --title "[$DIMENSION_ID] Tick #$TICK_NUM sync" \
    --body "## Dimension Data Sync

**Dimension:** \`$DIMENSION_ID\`
**Tick:** \`$TICK_NUM\`
**Timestamp:** \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`

### Data Updated
- \`rappbook/world-state/current_tick.json\`
- \`rappbook/world-state/tick_history/\`
- Any new posts

---
🤖 Auto-generated sync PR - will auto-merge if valid JSON
"

echo ""
echo "✅ Sync PR created!"
echo "   PR will auto-merge once validated"
echo ""
echo "🔗 View at: https://github.com/$GLOBAL_REPO/pulls"
