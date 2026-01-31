#!/usr/bin/env python3
"""
Copilot Steward Daemon - Background file organization agent
Runs continuously to detect and merge versioned duplicate files.

Usage:
    python3 scripts/copilot_steward_daemon.py                    # Run with defaults
    python3 scripts/copilot_steward_daemon.py --interval 300     # Check every 5 minutes
    python3 scripts/copilot_steward_daemon.py --once             # Single run then exit
    nohup python3 scripts/copilot_steward_daemon.py &            # Run in background
"""

import os
import sys
import time
import json
import signal
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Import the main steward functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from copilot_steward import (
    find_versioned_duplicates,
    merge_file_group,
    create_manifest,
    create_pr,
    SKIP_DIRS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [STEWARD] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('copilot-steward')

# Global flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info("Received shutdown signal, finishing current cycle...")
    running = False


def load_state(state_file):
    """Load previous daemon state."""
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'last_run': None,
        'total_merges': 0,
        'total_files_consolidated': 0,
        'prs_created': [],
        'errors': []
    }


def save_state(state_file, state):
    """Save daemon state."""
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def run_steward_cycle(root_path, auto_pr=False, repo='kody-w/CommunityRAPP'):
    """
    Run a single steward cycle: scan, merge, optionally create PR.
    Returns (merges_count, files_count, pr_url or None)
    """
    logger.info(f"Starting scan cycle for: {root_path}")
    
    groups = find_versioned_duplicates(root_path)
    
    # Filter to actual duplicates
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1 or 
                       (len(v) == 1 and v[0]['version'] > 0)}
    
    if not duplicate_groups:
        logger.info("No duplicates found - repository is clean")
        return 0, 0, None
    
    total_files = sum(len(v) for v in duplicate_groups.values())
    logger.info(f"Found {len(duplicate_groups)} duplicate groups ({total_files} files)")
    
    # Perform merges
    merges = []
    success_count = 0
    
    for (dirpath, canonical), versions in duplicate_groups.items():
        rel_canonical = os.path.relpath(os.path.join(dirpath, canonical), root_path)
        
        success, msg, canonical_path = merge_file_group(versions, dry_run=False)
        
        if success:
            logger.info(f"✅ Merged: {rel_canonical} - {msg}")
            success_count += 1
            merges.append({
                'canonical': rel_canonical,
                'sources': [v['filename'] for v in versions if v['version'] > 0],
                'strategy': 'union_by_id' if versions[0]['ext'] == '.json' else 'latest_version',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            logger.warning(f"❌ Failed: {rel_canonical} - {msg}")
    
    if not merges:
        return 0, 0, None
    
    # Create manifest
    manifest_path = create_manifest(merges, root_path)
    logger.info(f"Created manifest: {manifest_path}")
    
    # Create PR if requested and we have merges
    pr_url = None
    if auto_pr and merges:
        logger.info("Creating GitHub PR...")
        try:
            success, result = create_pr(root_path, merges, repo)
            if success:
                pr_url = result
                logger.info(f"✅ PR created: {pr_url}")
            else:
                logger.error(f"PR creation failed: {result}")
        except Exception as e:
            logger.error(f"PR creation error: {e}")
    
    files_consolidated = sum(len(m.get('sources', [])) for m in merges)
    return success_count, files_consolidated, pr_url


def daemon_loop(root_path, interval=300, auto_pr=False, repo='kody-w/CommunityRAPP'):
    """
    Main daemon loop - runs continuously.
    """
    global running
    
    state_file = os.path.join(root_path, '.steward-daemon-state.json')
    state = load_state(state_file)
    
    logger.info("=" * 60)
    logger.info("📚 Copilot Steward Daemon Starting")
    logger.info(f"   Root path: {root_path}")
    logger.info(f"   Interval: {interval} seconds")
    logger.info(f"   Auto-PR: {auto_pr}")
    logger.info(f"   Previous merges: {state['total_merges']}")
    logger.info("=" * 60)
    
    cycle_count = 0
    
    while running:
        cycle_count += 1
        logger.info(f"\n--- Cycle {cycle_count} ---")
        
        try:
            merges, files, pr_url = run_steward_cycle(root_path, auto_pr, repo)
            
            # Update state
            state['last_run'] = datetime.utcnow().isoformat() + 'Z'
            state['total_merges'] += merges
            state['total_files_consolidated'] += files
            if pr_url:
                state['prs_created'].append({
                    'url': pr_url,
                    'timestamp': state['last_run'],
                    'merges': merges
                })
            
            save_state(state_file, state)
            
            if merges > 0:
                logger.info(f"Cycle complete: {merges} groups merged, {files} files consolidated")
            else:
                logger.info("Cycle complete: No changes needed")
                
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            state['errors'].append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error': str(e)
            })
            save_state(state_file, state)
        
        if not running:
            break
            
        # Sleep until next cycle
        logger.info(f"Sleeping {interval} seconds until next cycle...")
        
        # Sleep in small increments to allow graceful shutdown
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)
    
    logger.info("=" * 60)
    logger.info("📚 Copilot Steward Daemon Shutting Down")
    logger.info(f"   Total cycles: {cycle_count}")
    logger.info(f"   Total merges: {state['total_merges']}")
    logger.info(f"   PRs created: {len(state['prs_created'])}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Copilot Steward Daemon - Background file organization agent'
    )
    parser.add_argument('--interval', type=int, default=300,
                       help='Seconds between scan cycles (default: 300 = 5 minutes)')
    parser.add_argument('--path', default='.',
                       help='Root path to monitor')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (no daemon loop)')
    parser.add_argument('--pr', action='store_true',
                       help='Auto-create PRs for merges')
    parser.add_argument('--repo', default='kody-w/CommunityRAPP',
                       help='GitHub repo for PRs')
    parser.add_argument('--log-file', 
                       help='Log to file instead of stdout')
    args = parser.parse_args()
    
    # Configure file logging if requested
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [STEWARD] %(levelname)s: %(message)s'
        ))
        logger.addHandler(file_handler)
    
    root_path = os.path.abspath(args.path)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if args.once:
        # Single run mode
        logger.info("Running single steward cycle...")
        merges, files, pr_url = run_steward_cycle(root_path, args.pr, args.repo)
        logger.info(f"Complete: {merges} groups merged, {files} files consolidated")
        if pr_url:
            logger.info(f"PR: {pr_url}")
        return 0
    else:
        # Daemon mode
        daemon_loop(root_path, args.interval, args.pr, args.repo)
        return 0


if __name__ == '__main__':
    sys.exit(main())
