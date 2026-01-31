---
name: automerge-agent
description: Monitor and auto-merge RAPPverse evolution PRs. Watches for open PRs, validates JSON, and merges them automatically. Use when PRs are piling up or auto-merge isn't working.
disable-model-invocation: false
---

# Automerge Agent

Monitors kody-w/openrapp for RAPPverse evolution PRs and merges them automatically.

## On Invocation

Run the automerge monitor:

```bash
cd /Users/kodywildfeuer/Documents/GitHub/m365-agents-for-python/openrapp
python3 scripts/automerge_agent.py
```

## What It Does

1. **Polls for open PRs** every 30 seconds
2. **Validates** PR is a world evolution PR (title starts with 🌍)
3. **Checks** PR is mergeable (no conflicts)
4. **Merges** using squash merge
5. **Cleans up** branch after merge
6. **Logs** all activity

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--interval` | 30 | Seconds between checks |
| `--dry-run` | false | Don't actually merge |
| `--repo` | kody-w/openrapp | Repository to monitor |

## Usage Examples

```bash
# Run continuously
python3 scripts/automerge_agent.py

# Check every 10 seconds
python3 scripts/automerge_agent.py --interval 10

# Dry run (just log what would happen)
python3 scripts/automerge_agent.py --dry-run

# Run in background
nohup python3 scripts/automerge_agent.py > /tmp/automerge.log 2>&1 &
```

## PR Validation

Only merges PRs that:
- Have title starting with `🌍 World Evolution`
- Are in mergeable state
- Have no merge conflicts
- Target the `main` branch

## Monitoring

```bash
# Check log
tail -f /tmp/automerge.log

# List merged PRs
gh pr list --repo kody-w/openrapp --state merged --limit 10
```

## Recovery Mode

If PRs pile up, run with faster interval:

```bash
python3 scripts/automerge_agent.py --interval 5
```

---

*Keeping the RAPPverse flowing smoothly*
