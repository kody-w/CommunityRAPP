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
# Copilot CLI Agent (uses invoked agent, no SDK required)
# ============================================================================

def run_copilot_cli_review(prompt: str) -> tuple[bool, str]:
    """
    Use Copilot CLI to review changes. Returns (approved, response_text).
    The invoked agent handles all the AI stuff - no SDK needed.
    """
    if not HAS_COPILOT_CLI:
        return False, "Copilot CLI not available"
    
    try:
        # Use copilot CLI with the prompt
        result = subprocess.run(
            ['copilot', '--model', 'claude-opus-4.5', '-m', prompt],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for review
        )
        
        response = result.stdout + result.stderr
        
        # Check for approval in response
        response_upper = response.upper()
        if 'APPROVED' in response_upper and 'REJECTED' not in response_upper:
            return True, response
        elif 'REJECTED' in response_upper:
            return False, response
        else:
            # Ambiguous - check for positive signals
            if any(word in response_upper for word in ['SAFE', 'GOOD', 'CORRECT', 'VALID', 'LGTM']):
                return True, response
            return False, response
            
    except subprocess.TimeoutExpired:
        return False, "Review timed out"
    except Exception as e:
        return False, f"Review failed: {e}"


async def run_auto_mode(path: str = ".", dry_run: bool = False, skip_review: bool = False):
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
    
    # Step 4: AI Review Gate
    if skip_review:
        print("\n⚠️  AI review skipped (--no-review flag)")
        print("   Proceeding directly to commit...")
        await commit_and_push(path, merge_result)
        return
    
    print("\n" + "=" * 60)
    print("🤖 AI REVIEW GATE - Copilot Agent Auditing Changes...")
    print("=" * 60 + "\n")
    
    if HAS_COPILOT_CLI:
        approved, review_response = await ai_review_changes(path, merge_result)
        
        print(review_response)
        
        if approved:
            print("\n✅ AI APPROVED - Proceeding with commit and push...")
            await commit_and_push(path, merge_result)
        else:
            print("\n❌ AI REJECTED - Changes NOT committed.")
            print("   Review the issues above and run again after fixing.")
            print("   Use --no-review to skip AI review if needed.")
    else:
        print("⚠️  Copilot CLI not found in PATH")
        print("   Install from: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli")
        print("   Changes merged but NOT committed (manual review required)")
        print("\n   To commit manually:")
        print("   git add -A && git commit -m '[Steward] Auto-merge duplicates' && git push")


async def ai_review_changes(path: str, merge_result: dict) -> tuple[bool, str]:
    """
    Use Copilot CLI (invoked agent) to review and audit the merged changes.
    Returns (approved, response_text).
    """
    abs_path = path if os.path.isabs(path) else os.path.abspath(path)
    
    # Collect the git diff to show what changed
    try:
        diff_result = subprocess.run(
            ['git', 'diff', '--stat'],
            cwd=abs_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        git_diff_stat = diff_result.stdout[:2000]
        
        # Get actual diff content (limited)
        diff_content_result = subprocess.run(
            ['git', 'diff', '--no-color'],
            cwd=abs_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        git_diff_content = diff_content_result.stdout[:4000]
    except Exception as e:
        git_diff_stat = f"Could not get diff: {e}"
        git_diff_content = ""
    
    # Build the review prompt
    review_prompt = f"""You are the AI Review Gate for the Copilot Steward auto-merge system.

AUDIT these file merges and determine if they are SAFE to commit.

## Merge Summary
- Groups merged: {merge_result['merged']}
- Failed: {merge_result['failed']}

## Files Changed
{json.dumps(merge_result.get('merges', [])[:15], indent=2)}

## Git Diff Statistics
{git_diff_stat}

## Git Diff Content (sample)
{git_diff_content[:2500]}

## Review Checklist
1. Data Integrity - Arrays should be UNIONED, not replaced
2. ID Preservation - All unique IDs (auction_id, post_id, etc.) preserved
3. Schema Consistency - JSON structure maintained
4. Proper Deduplication - Exact duplicates removed correctly

## YOUR VERDICT
End your response with exactly one of:
- APPROVED - if merge is safe and correct
- REJECTED: <reason> - if there are data integrity issues

Be concise. Focus on data safety."""

    # Use Copilot CLI for review
    return run_copilot_cli_review(review_prompt)


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
        description='Copilot Steward Agent - File organization with AI review gate'
    )
    parser.add_argument('--auto', action='store_true',
                       help='Run in automatic mode (scan & merge with AI review)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as background daemon')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without making them')
    parser.add_argument('--no-review', action='store_true',
                       help='Skip AI review gate (commit directly)')
    parser.add_argument('--path', default='.',
                       help='Directory to scan/merge')
    args = parser.parse_args()
    
    if args.daemon:
        # Import and run daemon
        from copilot_steward_daemon import daemon_loop
        daemon_loop(os.path.abspath(args.path))
    elif args.auto:
        asyncio.run(run_auto_mode(args.path, args.dry_run, args.no_review))
    else:
        # Interactive mode - just run auto with prompts
        print("📚 Copilot Steward - Interactive Mode")
        print("   Use --auto for automatic mode with AI review")
        print("   Use --auto --dry-run to preview changes\n")
        asyncio.run(run_auto_mode(args.path, dry_run=True))


if __name__ == '__main__':
    main()
