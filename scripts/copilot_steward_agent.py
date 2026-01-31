#!/usr/bin/env python3
"""
Copilot Steward Agent - SDK-powered background agent
Uses GitHub Copilot SDK to run as an intelligent background agent
that monitors and auto-merges versioned duplicate files.

Requires: pip install github-copilot-sdk

Usage:
    python3 scripts/copilot_steward_agent.py                    # Interactive mode
    python3 scripts/copilot_steward_agent.py --auto             # Auto-run steward
    python3 scripts/copilot_steward_agent.py --daemon           # Background daemon
"""

import asyncio
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from copilot import CopilotClient
    from copilot.tools import define_tool
    from copilot.generated.session_events import SessionEventType
    from pydantic import BaseModel, Field
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    print("⚠️  GitHub Copilot SDK not installed. Install with: pip install github-copilot-sdk")
    print("   Falling back to direct script execution.\n")

from copilot_steward import (
    find_versioned_duplicates,
    merge_file_group,
    create_manifest,
    SKIP_DIRS
)


# ============================================================================
# Tool Parameter Models (for Copilot SDK)
# ============================================================================

if HAS_SDK:
    class ScanParams(BaseModel):
        path: str = Field(default=".", description="Directory path to scan for duplicates")

    class MergeParams(BaseModel):
        path: str = Field(default=".", description="Directory path to merge duplicates in")
        dry_run: bool = Field(default=False, description="Preview changes without making them")

    class StatusParams(BaseModel):
        pass  # No parameters needed


# ============================================================================
# Steward Tool Implementations
# ============================================================================

def scan_for_duplicates(path: str = ".") -> dict:
    """Scan directory for versioned duplicate files."""
    root_path = os.path.abspath(path)
    groups = find_versioned_duplicates(root_path)
    
    # Filter to actual duplicates
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1 or 
                       (len(v) == 1 and v[0]['version'] > 0)}
    
    if not duplicate_groups:
        return {
            "status": "clean",
            "message": "No versioned duplicates found! Repository is clean.",
            "duplicate_groups": 0,
            "total_files": 0
        }
    
    total_files = sum(len(v) for v in duplicate_groups.values())
    
    # Format results
    groups_list = []
    for (dirpath, canonical), versions in sorted(duplicate_groups.items()):
        rel_dir = os.path.relpath(dirpath, root_path)
        groups_list.append({
            "directory": rel_dir,
            "canonical": canonical,
            "versions": [v['filename'] for v in sorted(versions, key=lambda x: x['version'])],
            "version_count": len(versions)
        })
    
    return {
        "status": "duplicates_found",
        "message": f"Found {len(duplicate_groups)} duplicate groups ({total_files} files)",
        "duplicate_groups": len(duplicate_groups),
        "total_files": total_files,
        "groups": groups_list[:20]  # Limit to first 20 for readability
    }


def merge_duplicates(path: str = ".", dry_run: bool = False) -> dict:
    """Merge versioned duplicate files into canonical versions."""
    root_path = os.path.abspath(path)
    groups = find_versioned_duplicates(root_path)
    
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1 or 
                       (len(v) == 1 and v[0]['version'] > 0)}
    
    if not duplicate_groups:
        return {
            "status": "nothing_to_merge",
            "message": "No duplicates to merge - repository is clean!",
            "merged": 0,
            "failed": 0
        }
    
    merges = []
    success_count = 0
    fail_count = 0
    
    for (dirpath, canonical), versions in duplicate_groups.items():
        rel_canonical = os.path.relpath(os.path.join(dirpath, canonical), root_path)
        
        success, msg, canonical_path = merge_file_group(versions, dry_run=dry_run, root_path=root_path)
        
        if success:
            success_count += 1
            merges.append({
                "canonical": rel_canonical,
                "sources": [v['filename'] for v in versions if v['version'] > 0],
                "message": msg
            })
        else:
            fail_count += 1
    
    # Create manifest if not dry run
    if not dry_run and merges:
        manifest_merges = [{
            'canonical': m['canonical'],
            'sources': m['sources'],
            'strategy': 'union_by_id',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        } for m in merges]
        create_manifest(manifest_merges, root_path)
    
    return {
        "status": "dry_run" if dry_run else "merged",
        "message": f"{'Would merge' if dry_run else 'Merged'} {success_count} groups, {fail_count} failed",
        "merged": success_count,
        "failed": fail_count,
        "merges": merges[:10]  # Limit output
    }


def get_steward_status() -> dict:
    """Get the current steward status and last run info."""
    manifest_path = ".steward-manifest.json"
    daemon_state_path = ".steward-daemon-state.json"
    
    status = {
        "agent": "copilot-steward",
        "version": "1.0.0",
        "last_manifest": None,
        "daemon_state": None
    }
    
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
                status["last_manifest"] = {
                    "last_run": manifest.get("last_run"),
                    "total_groups_merged": manifest.get("total_groups_merged"),
                    "total_files_consolidated": manifest.get("total_files_consolidated")
                }
        except:
            pass
    
    if os.path.exists(daemon_state_path):
        try:
            with open(daemon_state_path) as f:
                state = json.load(f)
                status["daemon_state"] = {
                    "last_run": state.get("last_run"),
                    "total_merges": state.get("total_merges"),
                    "prs_created": len(state.get("prs_created", []))
                }
        except:
            pass
    
    return status


# ============================================================================
# Copilot SDK Agent
# ============================================================================

async def run_copilot_agent():
    """Run the steward as a Copilot SDK-powered agent."""
    if not HAS_SDK:
        print("Copilot SDK not available. Use --auto for direct execution.")
        return
    
    # Define tools for Copilot
    @define_tool(description="Scan a directory for versioned duplicate files (e.g., 'file 5.json', 'file 6.json')")
    async def scan_duplicates(params: ScanParams) -> dict:
        return scan_for_duplicates(params.path)
    
    @define_tool(description="Merge versioned duplicate files into canonical master versions. Safe - backs up files first.")
    async def merge_duplicate_files(params: MergeParams) -> dict:
        return merge_duplicates(params.path, params.dry_run)
    
    @define_tool(description="Get the current steward status, last run info, and statistics")
    async def steward_status(params: StatusParams) -> dict:
        return get_steward_status()
    
    # Initialize Copilot client
    client = CopilotClient()
    await client.start()
    
    # Use Claude Opus 4.5 for best reasoning capability
    session = await client.create_session({
        "model": "claude-opus-4.5",
        "streaming": True,
        "tools": [scan_duplicates, merge_duplicate_files, steward_status],
        "system_message": {
            "content": """You are the Copilot Steward - an organizing librarian agent for the RAPPverse repository.

Your job is to keep the repository clean by finding and merging versioned duplicate files.

Files like 'active 5.json', 'active 6.json' should be merged into 'active.json'.
Files like 'README 3.md' should become 'README.md'.

When asked to clean up or organize, use your tools:
1. scan_duplicates - Find all versioned duplicates
2. merge_duplicate_files - Safely merge them (backs up first)
3. steward_status - Check your last run and stats

Be helpful, efficient, and explain what you're doing.
"""
        }
    })
    
    # Handle streaming output
    def handle_event(event):
        if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
            sys.stdout.write(event.data.delta_content)
            sys.stdout.flush()
        if event.type == SessionEventType.SESSION_IDLE:
            print()
    
    session.on(handle_event)
    
    print("📚 Copilot Steward Agent (powered by GitHub Copilot SDK)")
    print("   Commands: 'scan', 'merge', 'status', 'help', 'exit'\n")
    
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        
        if user_input.lower() in ('exit', 'quit', 'q'):
            break
        
        sys.stdout.write("Steward: ")
        await session.send_and_wait({"prompt": user_input})
        print()
    
    await client.stop()
    print("\n👋 Steward signing off!")


async def run_auto_mode(path: str = ".", dry_run: bool = False):
    """Run steward in automatic mode - scan and merge without interaction."""
    print("📚 Copilot Steward - Auto Mode")
    print(f"🔍 Scanning: {os.path.abspath(path)}")
    print()
    
    # Scan
    scan_result = scan_for_duplicates(path)
    print(f"📊 {scan_result['message']}")
    
    if scan_result['status'] == 'clean':
        print("✨ Nothing to do!")
        return
    
    print()
    for group in scan_result.get('groups', [])[:10]:
        print(f"  📁 {group['directory']}/")
        for v in group['versions']:
            print(f"     └── {v}")
        print(f"     → {group['canonical']}")
    
    if len(scan_result.get('groups', [])) > 10:
        print(f"  ... and {len(scan_result['groups']) - 10} more groups")
    
    print()
    
    # Merge
    if dry_run:
        print("🔄 DRY RUN - Preview only")
    else:
        print("🔄 Merging duplicates...")
    
    merge_result = merge_duplicates(path, dry_run)
    print(f"✅ {merge_result['message']}")
    
    if merge_result.get('merges'):
        print()
        for m in merge_result['merges'][:5]:
            print(f"  ✓ {m['canonical']}")


def main():
    parser = argparse.ArgumentParser(
        description='Copilot Steward Agent - SDK-powered file organization'
    )
    parser.add_argument('--auto', action='store_true',
                       help='Run in automatic mode (scan & merge)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as background daemon')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--path', default='.',
                       help='Directory to scan/merge')
    args = parser.parse_args()
    
    if args.daemon:
        # Import and run daemon
        from copilot_steward_daemon import daemon_loop
        daemon_loop(os.path.abspath(args.path))
    elif args.auto:
        asyncio.run(run_auto_mode(args.path, args.dry_run))
    else:
        if HAS_SDK:
            asyncio.run(run_copilot_agent())
        else:
            print("Install Copilot SDK for interactive mode: pip install github-copilot-sdk")
            print("Running auto mode instead...\n")
            asyncio.run(run_auto_mode(args.path, args.dry_run))


if __name__ == '__main__':
    main()
