#!/usr/bin/env python3
"""
Copilot Steward Agent - Background agent with AI Review Gate
Uses Copilot CLI (invoked agent) to review and audit merges before committing.

The invoked Copilot agent reviews all changes and must approve before any push occurs.
No SDK installation required - uses the Copilot CLI directly.

Usage:
    python3 scripts/copilot_steward_agent.py                    # Interactive mode
    python3 scripts/copilot_steward_agent.py --auto             # Auto with AI review
    python3 scripts/copilot_steward_agent.py --auto --dry-run   # Preview only
    python3 scripts/copilot_steward_agent.py --auto --no-review # Skip AI review
    python3 scripts/copilot_steward_agent.py --daemon           # Background daemon
"""

import asyncio
import sys
import os
import json
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copilot_steward import (
    find_versioned_duplicates,
    merge_file_group,
    create_manifest,
    SKIP_DIRS
)


# ============================================================================
# Check for Copilot CLI availability
# ============================================================================

def check_copilot_cli() -> bool:
    """Check if Copilot CLI is available."""
    try:
        result = subprocess.run(
            ['copilot', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

HAS_COPILOT_CLI = check_copilot_cli()


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
    """Run steward in automatic mode with AI review gate before commit."""
    print("📚 Copilot Steward - Auto Mode with AI Review Gate")
    print(f"🔍 Scanning: {os.path.abspath(path)}")
    print()
    
    # Step 1: Scan for duplicates
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
    
    # Step 2: Do a dry-run merge first to see what would change
    print("🔄 Running dry-run to preview changes...")
    dry_run_result = merge_duplicates(path, dry_run=True)
    print(f"📋 Preview: {dry_run_result['message']}")
    
    if dry_run:
        print("\n✅ Dry-run complete. No changes made.")
        return
    
    # Step 3: Actually merge the files (but don't commit yet)
    print("\n🔄 Executing merge (files only, no commit yet)...")
    merge_result = merge_duplicates(path, dry_run=False)
    print(f"✅ {merge_result['message']}")
    
    if merge_result['merged'] == 0:
        print("Nothing was merged.")
        return
    
    # Step 4: AI Review Gate - Claude Opus 4.5 reviews before commit
    print("\n" + "=" * 60)
    print("🤖 AI REVIEW GATE - Claude Opus 4.5 Auditing Changes...")
    print("=" * 60 + "\n")
    
    if HAS_SDK:
        approved = await ai_review_changes(path, merge_result)
        
        if approved:
            print("\n✅ AI APPROVED - Proceeding with commit and push...")
            await commit_and_push(path, merge_result)
        else:
            print("\n❌ AI REJECTED - Changes NOT committed.")
            print("   Review the issues above and run again after fixing.")
            # Optionally restore from backup here
    else:
        print("⚠️  Copilot SDK not installed - skipping AI review")
        print("   Install with: pip install github-copilot-sdk")
        print("   Changes merged but NOT committed (manual review required)")


async def ai_review_changes(path: str, merge_result: dict) -> bool:
    """
    Use Claude Opus 4.5 to review and audit the merged changes.
    Returns True if approved, False if rejected.
    """
    client = CopilotClient()
    await client.start()
    
    # Collect the git diff to show what changed
    try:
        diff_result = subprocess.run(
            ['git', 'diff', '--stat'],
            cwd=path if os.path.isabs(path) else os.path.abspath(path),
            capture_output=True,
            text=True,
            timeout=30
        )
        git_diff_stat = diff_result.stdout[:2000]  # Limit size
        
        # Get actual diff content (limited)
        diff_content_result = subprocess.run(
            ['git', 'diff', '--no-color'],
            cwd=path if os.path.isabs(path) else os.path.abspath(path),
            capture_output=True,
            text=True,
            timeout=30
        )
        git_diff_content = diff_content_result.stdout[:5000]  # Limit size
    except Exception as e:
        git_diff_stat = f"Could not get diff: {e}"
        git_diff_content = ""
    
    # Build the review prompt
    review_prompt = f"""You are the AI Review Gate for the Copilot Steward auto-merge system.

Your job is to AUDIT the following file merges and determine if they are SAFE to commit.

## Merge Summary
- Groups merged: {merge_result['merged']}
- Failed: {merge_result['failed']}

## Files Changed
{json.dumps(merge_result.get('merges', []), indent=2)}

## Git Diff Statistics
```
{git_diff_stat}
```

## Git Diff Content (truncated)
```diff
{git_diff_content[:3000]}
```

## Your Review Tasks
1. **Data Integrity**: Verify no data was lost in the merge. Arrays should be UNIONED, not replaced.
2. **ID Preservation**: Check that all unique IDs (auction_id, post_id, etc.) are preserved.
3. **Schema Consistency**: Ensure JSON structure is maintained.
4. **No Duplicates**: Verify exact duplicates were properly deduped.
5. **Backup Exists**: Confirm files were backed up before merge.

## Response Format
Respond with your analysis, then end with one of:
- **APPROVED** - if all checks pass and the merge is safe
- **REJECTED: <reason>** - if there are issues that need fixing

Be thorough but concise. Focus on data integrity."""

    session = await client.create_session({
        "model": "claude-opus-4.5",
        "streaming": True,
    })
    
    response_text = []
    approved = False
    
    def handle_event(event):
        nonlocal approved
        if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
            content = event.data.delta_content
            sys.stdout.write(content)
            sys.stdout.flush()
            response_text.append(content)
    
    session.on(handle_event)
    
    await session.send_and_wait({"prompt": review_prompt})
    print()
    
    await client.stop()
    
    # Parse the response for approval
    full_response = ''.join(response_text).upper()
    if 'APPROVED' in full_response and 'REJECTED' not in full_response:
        approved = True
    elif 'REJECTED' in full_response:
        approved = False
    else:
        # Ambiguous - default to not approved for safety
        print("\n⚠️  AI response was ambiguous - defaulting to NOT approved for safety")
        approved = False
    
    return approved


async def commit_and_push(path: str, merge_result: dict):
    """Commit and push the approved changes."""
    abs_path = path if os.path.isabs(path) else os.path.abspath(path)
    
    try:
        # Stage all changes
        subprocess.run(['git', 'add', '-A'], cwd=abs_path, check=True)
        
        # Create commit message
        commit_msg = f"""[Steward] Auto-merge {merge_result['merged']} duplicate file groups

AI Review: APPROVED by Claude Opus 4.5

Merged files:
{chr(10).join(['- ' + m['canonical'] for m in merge_result.get('merges', [])[:10]])}
{'... and more' if len(merge_result.get('merges', [])) > 10 else ''}

---
Auto-generated by Copilot Steward with AI review gate
"""
        
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=abs_path,
            check=True
        )
        print("✅ Changes committed")
        
        # Push
        result = subprocess.run(
            ['git', 'push'],
            cwd=abs_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Changes pushed successfully!")
        else:
            print(f"⚠️  Push failed: {result.stderr}")
            print("   You may need to push manually: git push")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        print("   Changes are staged but not committed/pushed")


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
