#!/usr/bin/env python3
"""
Copilot Steward - The Organizing Librarian
Auto-merges versioned duplicate files into master versions via GitHub PRs.

Usage:
    python3 scripts/copilot_steward.py --scan              # List all duplicates
    python3 scripts/copilot_steward.py --auto              # Auto-merge all
    python3 scripts/copilot_steward.py --pr                # Create PR with merges
    python3 scripts/copilot_steward.py --path CommunityRAPP # Limit to directory
    python3 scripts/copilot_steward.py --dry-run           # Preview changes
"""

import os
import sys
import json
import shutil
import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict


SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.pytest_cache', '.archive', '.steward-backup'}

BACKUP_DIR = '.steward-backup'


def find_versioned_duplicates(root_path):
    """
    Find all files with version suffixes like 'filename 5.json', 'filename 6.json'.
    Groups them by their canonical (non-versioned) base name.
    """
    pattern = re.compile(r'^(.+) (\d+)(\.[\w]+)?$')
    groups = defaultdict(list)
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        
        for filename in filenames:
            match = pattern.match(filename)
            if match:
                base_name = match.group(1)
                version_num = int(match.group(2))
                ext = match.group(3) or ''
                canonical = base_name + ext
                full_path = os.path.join(dirpath, filename)
                canonical_path = os.path.join(dirpath, canonical)
                
                groups[(dirpath, canonical)].append({
                    'path': full_path,
                    'filename': filename,
                    'version': version_num,
                    'ext': ext,
                    'canonical_path': canonical_path
                })
    
    # Also check if canonical version exists
    for (dirpath, canonical), versions in groups.items():
        canonical_path = os.path.join(dirpath, canonical)
        if os.path.exists(canonical_path):
            versions.append({
                'path': canonical_path,
                'filename': canonical,
                'version': 0,  # Canonical is version 0
                'ext': versions[0]['ext'] if versions else '',
                'canonical_path': canonical_path
            })
        # Sort by version number
        versions.sort(key=lambda x: x['version'])
    
    return groups


def merge_json_by_id(data_list, id_fields=None):
    """
    Merge multiple JSON data structures, unioning arrays by ID.
    """
    if id_fields is None:
        id_fields = ['id', 'auction_id', 'post_id', 'card_id', 'bid_id', 'mystery_id', 'bounty_id']
    
    if not data_list:
        return {}
    
    if isinstance(data_list[0], list):
        # Merge arrays
        return merge_arrays_by_id([item for data in data_list for item in data], id_fields)
    
    if isinstance(data_list[0], dict):
        result = {}
        all_keys = set()
        for data in data_list:
            all_keys.update(data.keys())
        
        for key in all_keys:
            values = [data.get(key) for data in data_list if key in data]
            if not values:
                continue
            
            # Check if values are lists - merge by ID
            if all(isinstance(v, list) for v in values):
                merged_list = []
                for v in values:
                    merged_list.extend(v)
                result[key] = merge_arrays_by_id(merged_list, id_fields)
            # Check if values are dicts - recurse
            elif all(isinstance(v, dict) for v in values):
                result[key] = merge_json_by_id(values, id_fields)
            else:
                # Scalar - take from highest version (last in list)
                result[key] = values[-1]
        
        return result
    
    # Scalar - return latest
    return data_list[-1]


def merge_arrays_by_id(items, id_fields):
    """
    Union array items by ID field, intelligently deduping.
    - Same ID + same content = dedupe (keep one)
    - Same ID + different content = keep latest by timestamp/tick
    - No ID = dedupe by content hash
    """
    if not items:
        return []
    
    # If items are simple types, just dedupe
    if not isinstance(items[0], dict):
        seen = []
        for item in items:
            if item not in seen:
                seen.append(item)
        return seen
    
    seen = {}
    for item in items:
        # Find ID from known ID fields
        item_id = None
        for field in id_fields:
            if field in item:
                item_id = item[field]
                break
        
        if item_id is None:
            # No ID field - generate hash from content (excluding timestamps)
            item_copy = {k: v for k, v in item.items() 
                        if k not in ('timestamp', 'last_updated', 'created_at', 'updated_at')}
            try:
                item_id = f"hash_{hash(json.dumps(item_copy, sort_keys=True))}"
            except:
                item_id = f"hash_{id(item)}"
        
        if item_id not in seen:
            seen[item_id] = item
        else:
            # Duplicate ID found - keep the one with more data or latest timestamp
            existing = seen[item_id]
            
            # Check if content is identical (true duplicate)
            if json.dumps(item, sort_keys=True) == json.dumps(existing, sort_keys=True):
                continue  # Exact duplicate, skip
            
            # Different content - pick the better one
            new_ts = item.get('timestamp', item.get('last_updated', item.get('created_at', '')))
            old_ts = existing.get('timestamp', existing.get('last_updated', existing.get('created_at', '')))
            new_tick = item.get('tick', item.get('current_tick', 0)) or 0
            old_tick = existing.get('tick', existing.get('current_tick', 0)) or 0
            
            # Prefer: higher tick > later timestamp > more fields
            if new_tick > old_tick:
                seen[item_id] = item
            elif new_tick == old_tick and new_ts > old_ts:
                seen[item_id] = item
            elif new_tick == old_tick and new_ts == old_ts and len(item) > len(existing):
                seen[item_id] = item
    
    # Sort results for consistent output
    result = list(seen.values())
    try:
        # Try to sort by ID field, then by timestamp
        def sort_key(x):
            for field in id_fields:
                if field in x:
                    return (0, str(x[field]))
            return (1, x.get('timestamp', ''))
        result.sort(key=sort_key)
    except:
        pass
    
    return result


def backup_files(versions, root_path):
    """
    Backup all version files before merging.
    Returns backup directory path.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_base = os.path.join(root_path, BACKUP_DIR, timestamp)
    os.makedirs(backup_base, exist_ok=True)
    
    for v in versions:
        if os.path.exists(v['path']):
            # Preserve relative path structure in backup
            rel_path = os.path.relpath(v['path'], root_path)
            backup_path = os.path.join(backup_base, rel_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(v['path'], backup_path)
    
    return backup_base


def merge_file_group(versions, dry_run=False, root_path='.'):
    """
    Merge a group of versioned files into the canonical version.
    SAFE: Always backs up files before merging to prevent data loss.
    Returns (success, message, canonical_path)
    """
    if not versions:
        return False, "No versions to merge", None
    
    canonical_path = versions[0]['canonical_path']
    ext = versions[0]['ext']
    
    # Sort by version (highest last = most recent)
    versions = sorted(versions, key=lambda x: x['version'])
    
    if dry_run:
        return True, f"Would merge {len(versions)} versions", canonical_path
    
    try:
        # SAFETY: Backup all files before any merge operation
        backup_path = backup_files(versions, root_path)
        if ext == '.json':
            # JSON merge
            data_list = []
            for v in versions:
                try:
                    with open(v['path'], 'r') as f:
                        data_list.append(json.load(f))
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ Skipping invalid JSON: {v['filename']} - {e}")
                    continue
            
            if not data_list:
                return False, "No valid JSON files to merge", canonical_path
            
            merged = merge_json_by_id(data_list)
            
            # Update metadata
            if isinstance(merged, dict):
                merged['last_updated'] = datetime.utcnow().isoformat() + 'Z'
                merged['_merged_by'] = 'copilot-steward'
                merged['_merged_from'] = [v['filename'] for v in versions]
            
            with open(canonical_path, 'w') as f:
                json.dump(merged, f, indent=2)
            
            msg = f"Merged {len(data_list)} JSON files"
        
        elif ext in ['.md', '.txt']:
            # Markdown/text - take highest version
            highest = max(versions, key=lambda x: x['version'])
            if highest['path'] != canonical_path:
                shutil.copy2(highest['path'], canonical_path)
            msg = f"Took version {highest['version']} as canonical"
        
        else:
            # Other files - take highest version
            highest = max(versions, key=lambda x: x['version'])
            if highest['path'] != canonical_path:
                shutil.copy2(highest['path'], canonical_path)
            msg = f"Took version {highest['version']} as canonical"
        
        # Delete versioned duplicates (not the canonical)
        for v in versions:
            if v['path'] != canonical_path and os.path.exists(v['path']):
                os.remove(v['path'])
        
        return True, msg, canonical_path
    
    except Exception as e:
        return False, f"Error: {e}", canonical_path


def create_manifest(merges, root_path):
    """Create a manifest file documenting all merges."""
    manifest = {
        'last_run': datetime.utcnow().isoformat() + 'Z',
        'agent': 'copilot-steward',
        'merges': merges,
        'total_groups_merged': len(merges),
        'total_files_consolidated': sum(len(m.get('sources', [])) for m in merges)
    }
    
    manifest_path = os.path.join(root_path, '.steward-manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_path


def create_pr(root_path, merges, repo='kody-w/CommunityRAPP'):
    """Create a GitHub PR with the merged changes."""
    os.chdir(root_path)
    
    branch_name = f"steward/merge-duplicates-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Create branch
    subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
    
    # Stage all changes
    subprocess.run(['git', 'add', '-A'], check=True)
    
    # Create commit message
    file_summary = '\n'.join([f"- {m['canonical']}" for m in merges[:10]])
    if len(merges) > 10:
        file_summary += f"\n- ... and {len(merges) - 10} more"
    
    commit_msg = f"""[Steward] Merge {len(merges)} duplicate file groups

Merged files:
{file_summary}

Total: {sum(len(m.get('sources', [])) for m in merges)} files consolidated into {len(merges)} master versions

---
*Auto-generated by Copilot Steward*"""
    
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    
    # Push
    subprocess.run(['git', 'push', 'origin', branch_name], check=True)
    
    # Create PR
    pr_body = f"""## 📚 Copilot Steward - Auto-Merge Report

Automatically merged versioned duplicate files into master versions.

### 📊 Summary
- **Groups merged:** {len(merges)}
- **Files consolidated:** {sum(len(m.get('sources', [])) for m in merges)}

### 📁 Changes

| Canonical File | Sources Merged | Strategy |
|----------------|----------------|----------|
"""
    
    for m in merges:
        sources = ', '.join([os.path.basename(s) for s in m.get('sources', [])])
        pr_body += f"| `{m['canonical']}` | {sources} | {m.get('strategy', 'auto')} |\n"
    
    pr_body += """
### 🔀 Merge Strategy
- **JSON arrays**: Union by ID field (auction_id, post_id, etc.)
- **JSON objects**: Deep merge, latest timestamp wins
- **Markdown/text**: Take highest version number
- **Other files**: Take highest version number

---
*Generated by Copilot Steward - The Organizing Librarian*
"""
    
    result = subprocess.run(
        ['gh', 'pr', 'create', 
         '--title', f'[Steward] Auto-merge {len(merges)} duplicate file groups',
         '--body', pr_body,
         '--repo', repo],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        pr_url = result.stdout.strip()
        return True, pr_url
    else:
        return False, result.stderr


def main():
    parser = argparse.ArgumentParser(
        description='Copilot Steward - Auto-merge versioned duplicate files'
    )
    parser.add_argument('--scan', action='store_true', 
                       help='List all duplicate groups')
    parser.add_argument('--auto', action='store_true', 
                       help='Auto-merge all duplicates')
    parser.add_argument('--pr', action='store_true', 
                       help='Create GitHub PR with merges')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without making them')
    parser.add_argument('--path', default='.', 
                       help='Root path to scan (default: current directory)')
    parser.add_argument('--repo', default='kody-w/CommunityRAPP',
                       help='GitHub repo for PR creation')
    args = parser.parse_args()
    
    root_path = os.path.abspath(args.path)
    print(f"📚 Copilot Steward - The Organizing Librarian")
    print(f"🔍 Scanning for versioned duplicates in: {root_path}")
    print()
    
    groups = find_versioned_duplicates(root_path)
    
    if not groups:
        print("✨ No versioned duplicates found! Repository is clean.")
        return 0
    
    # Filter to groups with actual duplicates (>1 version)
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1 or 
                       (len(v) == 1 and v[0]['version'] > 0)}
    
    if not duplicate_groups:
        print("✨ No versioned duplicates found! Repository is clean.")
        return 0
    
    total_files = sum(len(v) for v in duplicate_groups.values())
    print(f"📋 Found {len(duplicate_groups)} duplicate groups ({total_files} files):")
    print()
    
    # Display groups
    for (dirpath, canonical), versions in sorted(duplicate_groups.items()):
        rel_dir = os.path.relpath(dirpath, root_path)
        print(f"📁 {rel_dir}/")
        for v in sorted(versions, key=lambda x: x['version']):
            marker = "└──" if v == versions[-1] else "├──"
            ver_label = f"(v{v['version']})" if v['version'] > 0 else "(master)"
            print(f"  {marker} {v['filename']} {ver_label}")
        print(f"  → Merge to: {canonical}")
        print()
    
    if args.scan or (not args.auto and not args.pr):
        print("─" * 60)
        print(f"📊 Total: {len(duplicate_groups)} groups, {total_files} files to consolidate")
        print()
        print("Commands:")
        print("  --auto       Auto-merge all duplicates")
        print("  --pr         Create GitHub PR with merges")
        print("  --dry-run    Preview changes")
        return 0
    
    # Perform merges
    print("─" * 60)
    print(f"{'🔄 DRY RUN: ' if args.dry_run else ''}Starting merge process...")
    print()
    
    merges = []
    success_count = 0
    fail_count = 0
    
    for (dirpath, canonical), versions in duplicate_groups.items():
        rel_canonical = os.path.relpath(os.path.join(dirpath, canonical), root_path)
        print(f"📝 Merging: {rel_canonical}")
        
        success, msg, canonical_path = merge_file_group(versions, dry_run=args.dry_run, root_path=root_path)
        
        if success:
            print(f"  ✅ {msg}")
            success_count += 1
            merges.append({
                'canonical': rel_canonical,
                'sources': [v['filename'] for v in versions if v['version'] > 0],
                'strategy': 'union_by_id' if versions[0]['ext'] == '.json' else 'latest_version',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
        else:
            print(f"  ❌ {msg}")
            fail_count += 1
    
    print()
    print("─" * 60)
    print(f"✅ Merged: {success_count}")
    print(f"❌ Failed: {fail_count}")
    
    if not args.dry_run and merges:
        # Create manifest
        manifest_path = create_manifest(merges, root_path)
        print(f"📋 Created manifest: {os.path.relpath(manifest_path, root_path)}")
        
        if args.pr:
            print()
            print("🔀 Creating GitHub PR...")
            success, result = create_pr(root_path, merges, args.repo)
            if success:
                print(f"✅ PR created: {result}")
            else:
                print(f"❌ PR creation failed: {result}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
