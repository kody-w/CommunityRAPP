---
name: copilot-steward
description: Organizing librarian that auto-merges versioned duplicate files (e.g., "active 5.json", "active 6.json") into master versions via GitHub PRs. Use when asked to clean up, organize, consolidate, or merge duplicate files.
disable-model-invocation: false
---

# Copilot Steward - The Organizing Librarian

An intelligent agent that discovers, analyzes, and auto-merges duplicate versioned files into canonical master versions, keeping the repository clean and organized.

## Quick Start

```bash
# Scan for duplicates
python3 scripts/copilot_steward.py --scan

# Auto-merge all duplicates
python3 scripts/copilot_steward.py --auto

# Create GitHub PR with merges
python3 scripts/copilot_steward.py --auto --pr

# Dry-run to preview changes
python3 scripts/copilot_steward.py --auto --dry-run

# Target specific directory
python3 scripts/copilot_steward.py --path CommunityRAPP --auto
```

## Problem Statement

The repository accumulates versioned duplicates of files:
- `active 5.json`, `active 6.json` → should be `active.json`
- `config 4.json`, `config 5.json` → should be `config.json`
- `README 3.md`, `README 4.md` → should be `README.md`

These are often created by sync conflicts or parallel editing. The Steward intelligently merges them.

## Arguments

`$ARGUMENTS` - Optional parameters:
- `--dry-run` - Report what would be merged without making changes
- `--path <dir>` - Limit scan to specific directory
- `--pr` - Create PR instead of direct commit
- `--force` - Merge even if conflicts detected (use latest version)

## Execution Flow

### 1. Scan for Duplicates

Find files matching the versioned pattern:
```bash
# Pattern: "filename N.ext" where N is a number
find . -type f -regex '.*[[:space:]][0-9]+\.[a-zA-Z]+$' 2>/dev/null | grep -v node_modules | grep -v .git
```

### 2. Group by Base Name

Group files by their canonical name:
```
active 5.json, active 6.json → base: "active.json"
history 5.json, history 6.json → base: "history.json"
```

### 3. Analyze Each Group

For each group of duplicates:

1. **Check for master file** - Does `active.json` (without version) exist?
2. **Compare versions** - Find highest version number
3. **Detect data type**:
   - JSON: Compare structure, merge arrays, take latest scalars
   - Markdown: Use latest version (highest number)
   - Config files: Merge carefully, prefer explicit values

### 4. Intelligent Merge Strategy

#### For JSON Data Files (auctions, posts, cards):

```python
def merge_json_files(versions):
    """
    Merge strategy for RAPPverse JSON data:
    - Arrays: Union by unique ID field
    - Objects: Deep merge, latest timestamp wins
    - Scalars: Take from highest version
    """
    merged = {}
    
    # Sort versions by number (highest = most recent)
    sorted_versions = sorted(versions, key=lambda x: x.version_num, reverse=True)
    
    for version in sorted_versions:
        data = json.load(version.path)
        deep_merge(merged, data, prefer_existing=False)
    
    return merged
```

#### For Arrays with IDs (auctions, bids, transactions):
```python
def merge_arrays_by_id(arr1, arr2, id_field="id"):
    """Union arrays, dedupe by ID, sort by timestamp if available"""
    seen = {}
    for item in arr1 + arr2:
        item_id = item.get(id_field) or item.get("auction_id") or item.get("bid_id")
        if item_id:
            # Keep item with latest timestamp
            if item_id not in seen or item.get("timestamp", "") > seen[item_id].get("timestamp", ""):
                seen[item_id] = item
    return list(seen.values())
```

#### For Markdown/Documentation:
- Take the highest versioned file as canonical
- Archive older versions if significantly different

### 5. Create Merged Master

Write the merged content to the canonical filename (without version number).

### 6. Archive or Delete Duplicates

Options:
- **Delete**: Remove versioned files after merge
- **Archive**: Move to `.archive/` directory with timestamp
- **Keep**: Leave originals (creates `.steward-merged` marker)

### 7. Create GitHub PR

If `--pr` flag or by default for CommunityRAPP:

```bash
cd CommunityRAPP
git checkout -b steward/merge-duplicates-$(date +%Y%m%d-%H%M%S)
git add -A
git commit -m "[Steward] Merge duplicate files

Merged files:
- auctions/active.json (from active 5.json, active 6.json)
- mysteries/active.json (from active 2.json, active 5.json, active 6.json)
- bounties/active.json (from active 4.json, active 5.json)

Total: X files consolidated into Y master versions"

git push origin HEAD
gh pr create --title "[Steward] Auto-merge duplicate files" \
  --body "## Summary
  
Automatically merged versioned duplicate files into master versions.

### Changes
- Consolidated X duplicate file groups
- Preserved all unique data through intelligent merging
- Archived original versions in .archive/

### Merge Strategy
- JSON arrays: Union by ID
- Objects: Deep merge with timestamp preference  
- Scalars: Latest version wins

---
*Generated by Copilot Steward*"
```

## File Type Handlers

### JSON Data Files

| Pattern | Merge Strategy |
|---------|----------------|
| `active*.json` | Merge auctions array by auction_id |
| `history*.json` | Append completed auctions, dedupe |
| `records*.json` | Union all records by id |
| `config*.json` | Deep merge, prefer explicit values |
| `current_tick*.json` | Take highest tick number |

### Markdown Files

| Pattern | Merge Strategy |
|---------|----------------|
| `README*.md` | Take highest version |
| `SKILL*.md` | Take highest version |
| Documentation | Take highest, diff for review |

### Config Files

| Pattern | Merge Strategy |
|---------|----------------|
| `package*.json` | Merge dependencies, take latest scripts |
| `*.config*.js` | Take highest version |
| `settings*.json` | Deep merge |

## Example Session

```
🔍 Scanning repository for versioned duplicates...

Found 23 duplicate groups:

📁 CommunityRAPP/rappbook/auctions/
  ├── active 5.json (tick 15)
  ├── active 6.json (tick 18)
  └── → Merge to: active.json

📁 CommunityRAPP/rappbook/mysteries/
  ├── active 2.json (3 mysteries)
  ├── active 5.json (4 mysteries)  
  ├── active 6.json (5 mysteries)
  └── → Merge to: active.json (7 unique mysteries)

📁 docs/
  ├── ARCHITECTURE 2.md (v1.0)
  └── → Merge to: ARCHITECTURE.md

Proceed with merge? [y/n/dry-run]: y

✅ Merged 23 file groups
✅ Created PR #47: "[Steward] Auto-merge duplicate files"
✅ Archived 42 original files to .archive/
```

## Conflict Resolution

When true conflicts exist (same ID, different data):

1. **Timestamp wins**: If both have timestamps, keep newer
2. **Tick wins**: If both have tick numbers, keep higher
3. **Interactive**: If no clear winner, prompt for decision
4. **Force mode**: `--force` always takes highest version number

## Safety Features

- Never deletes without backup
- Creates `.steward-manifest.json` tracking all merges
- Supports rollback via git history
- Dry-run mode for preview
- Skips files in `.gitignore`

## Integration

The Steward can be invoked:
- Manually: `invoke copilot-steward`
- On schedule: Via GitHub Actions cron
- Pre-commit: As a git hook
- Post-evolution: Called by rappbook-evolver after ticks

## Manifest File

Creates `.steward-manifest.json`:
```json
{
  "last_run": "2026-01-31T18:00:00Z",
  "merges": [
    {
      "canonical": "auctions/active.json",
      "sources": ["auctions/active 5.json", "auctions/active 6.json"],
      "strategy": "union_by_id",
      "items_merged": 5,
      "timestamp": "2026-01-31T18:00:00Z"
    }
  ],
  "archived_files": [],
  "total_space_saved_kb": 42
}
```

---

*Copilot Steward - Keeper of the Repository Order*
