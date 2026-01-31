#!/usr/bin/env python3
"""
Automerge Agent - Monitors and auto-merges RAPPverse evolution PRs.

Monitors kody-w/CommunityRAPP for world evolution PRs and merges them.

Usage:
    python3 automerge_agent.py                # Run continuously
    python3 automerge_agent.py --interval 10  # Check every 10 seconds
    python3 automerge_agent.py --dry-run      # Don't actually merge
"""

import subprocess
import json
import time
import argparse
from datetime import datetime


def log(message):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_open_prs(repo):
    """Get list of open PRs from the repository."""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--json", 
             "number,title,state,mergeable,headRefName,baseRefName"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        log(f"❌ Error fetching PRs: {e}")
        return []
    except json.JSONDecodeError:
        log("❌ Error parsing PR list")
        return []


def is_evolution_pr(pr):
    """Check if PR is a RAPPverse evolution PR."""
    title = pr.get("title", "")
    return title.startswith("🌍 World Evolution")


def can_merge(pr):
    """Check if PR can be merged."""
    mergeable = pr.get("mergeable", "")
    base = pr.get("baseRefName", "")
    return mergeable == "MERGEABLE" and base == "main"


def merge_pr(repo, pr_number, dry_run=False):
    """Merge a PR using squash merge."""
    if dry_run:
        log(f"🔸 [Dry run] Would merge PR #{pr_number}")
        return True
    
    try:
        result = subprocess.run(
            ["gh", "pr", "merge", str(pr_number), "--repo", repo, 
             "--squash", "--delete-branch"],
            capture_output=True,
            text=True,
            check=True
        )
        log(f"✅ Merged PR #{pr_number}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Failed to merge PR #{pr_number}: {e.stderr}")
        return False


def run_agent(repo, interval=30, dry_run=False):
    """Run the automerge agent continuously."""
    log("🤖 Automerge Agent Starting...")
    log(f"   Repository: {repo}")
    log(f"   Check interval: {interval}s")
    log(f"   Dry run: {dry_run}")
    log("   Press Ctrl+C to stop\n")
    
    total_merged = 0
    
    try:
        while True:
            prs = get_open_prs(repo)
            
            if not prs:
                log("📭 No open PRs")
            else:
                log(f"📬 Found {len(prs)} open PR(s)")
                
                for pr in prs:
                    pr_num = pr.get("number")
                    title = pr.get("title", "")[:50]
                    
                    if not is_evolution_pr(pr):
                        log(f"   ⏭️  PR #{pr_num}: Not an evolution PR, skipping")
                        continue
                    
                    if not can_merge(pr):
                        mergeable = pr.get("mergeable", "UNKNOWN")
                        log(f"   ⏸️  PR #{pr_num}: Not mergeable ({mergeable})")
                        continue
                    
                    log(f"   🔄 PR #{pr_num}: {title}...")
                    if merge_pr(repo, pr_num, dry_run):
                        total_merged += 1
            
            log(f"💤 Sleeping {interval}s... (Total merged: {total_merged})\n")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        log(f"\n\n⏹️  Agent stopped. Total PRs merged: {total_merged}")


def main():
    parser = argparse.ArgumentParser(description="Automerge Agent for RAPPverse")
    parser.add_argument("--repo", default="kody-w/CommunityRAPP", 
                        help="Repository to monitor (default: kody-w/CommunityRAPP)")
    parser.add_argument("--interval", type=int, default=15,
                        help="Seconds between checks (default: 15)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually merge, just log")
    
    args = parser.parse_args()
    run_agent(args.repo, args.interval, args.dry_run)


if __name__ == "__main__":
    main()
