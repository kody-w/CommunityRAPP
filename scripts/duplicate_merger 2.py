#!/usr/bin/env python3
"""
Duplicate File Merger for RAPPverse
Finds files/folders with " 2", " 3" suffixes and intelligently merges them.

Usage:
    python3 scripts/duplicate_merger.py --scan          # List all duplicates
    python3 scripts/duplicate_merger.py --auto          # Auto-merge safe cases
    python3 scripts/duplicate_merger.py --interactive   # Guide through each merge
"""

import os
import sys
import json
import shutil
import argparse
import re
from pathlib import Path
from datetime import datetime

# Skip these directories (generated/vendored)
SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.pytest_cache'}

def find_duplicates(root_path, include_orphans=True):
    """Find all files/folders with ' 2', ' 3' etc suffixes."""
    duplicates = []
    orphans = []
    pattern = re.compile(r'^(.+) (\d+)(\..*)?$')
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip vendored directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        
        # Check directories
        for dirname in list(dirnames):
            match = pattern.match(dirname)
            if match:
                base_name = match.group(1)
                suffix_num = match.group(2)
                original_path = os.path.join(dirpath, base_name)
                dup_path = os.path.join(dirpath, dirname)
                entry = {
                    'type': 'directory',
                    'original': original_path,
                    'duplicate': dup_path,
                    'suffix': suffix_num,
                    'orphan': not os.path.exists(original_path)
                }
                if os.path.exists(original_path):
                    duplicates.append(entry)
                elif include_orphans:
                    orphans.append(entry)
        
        # Check files
        for filename in filenames:
            match = pattern.match(filename)
            if match:
                base_name = match.group(1)
                suffix_num = match.group(2)
                ext = match.group(3) or ''
                original_path = os.path.join(dirpath, base_name + ext)
                dup_path = os.path.join(dirpath, filename)
                entry = {
                    'type': 'file',
                    'original': original_path,
                    'duplicate': dup_path,
                    'suffix': suffix_num,
                    'ext': ext,
                    'orphan': not os.path.exists(original_path)
                }
                if os.path.exists(original_path):
                    duplicates.append(entry)
                elif include_orphans:
                    orphans.append(entry)
    
    return duplicates + orphans

def merge_json_files(original_path, duplicate_path):
    """Merge two JSON files intelligently."""
    try:
        with open(original_path, 'r') as f:
            orig_data = json.load(f)
        with open(duplicate_path, 'r') as f:
            dup_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    
    merged = deep_merge(orig_data, dup_data)
    
    with open(original_path, 'w') as f:
        json.dump(merged, f, indent=2)
    
    return True, "JSON merged successfully"

def deep_merge(base, overlay):
    """Deep merge two dicts/lists."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = base.copy()
        for key, value in overlay.items():
            if key in result:
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    elif isinstance(base, list) and isinstance(overlay, list):
        # Combine lists, removing duplicates for simple types
        combined = base.copy()
        for item in overlay:
            if item not in combined:
                combined.append(item)
        return combined
    else:
        # Prefer overlay (newer)
        return overlay

def merge_text_files(original_path, duplicate_path):
    """Merge two text files, keeping unique lines."""
    with open(original_path, 'r') as f:
        orig_lines = f.readlines()
    with open(duplicate_path, 'r') as f:
        dup_lines = f.readlines()
    
    # If files are identical, just return
    if orig_lines == dup_lines:
        return True, "Files identical"
    
    # For markdown/text, append unique content from duplicate
    orig_set = set(orig_lines)
    new_lines = [line for line in dup_lines if line not in orig_set]
    
    if new_lines:
        with open(original_path, 'a') as f:
            f.write('\n<!-- Merged from duplicate -->\n')
            f.writelines(new_lines)
        return True, f"Added {len(new_lines)} unique lines"
    
    return True, "No unique content in duplicate"

def merge_directories(original_path, duplicate_path):
    """Merge two directories."""
    merged_count = 0
    
    for item in os.listdir(duplicate_path):
        dup_item_path = os.path.join(duplicate_path, item)
        orig_item_path = os.path.join(original_path, item)
        
        if os.path.exists(orig_item_path):
            # Both exist - recurse or merge
            if os.path.isdir(dup_item_path) and os.path.isdir(orig_item_path):
                merge_directories(orig_item_path, dup_item_path)
            elif os.path.isfile(dup_item_path) and os.path.isfile(orig_item_path):
                # Merge files
                if item.endswith('.json'):
                    merge_json_files(orig_item_path, dup_item_path)
                else:
                    merge_text_files(orig_item_path, dup_item_path)
        else:
            # Only in duplicate - move to original
            shutil.move(dup_item_path, orig_item_path)
        merged_count += 1
    
    return True, f"Merged {merged_count} items"

def auto_merge(dup_info, dry_run=False):
    """Automatically merge a duplicate."""
    dup_type = dup_info['type']
    original = dup_info['original']
    duplicate = dup_info['duplicate']
    is_orphan = dup_info.get('orphan', False)
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}{'Renaming orphan' if is_orphan else 'Merging'}: {os.path.basename(duplicate)}")
    print(f"  Original: {original} {'(missing)' if is_orphan else ''}")
    print(f"  Duplicate: {duplicate}")
    
    if dry_run:
        return True, "Would merge"
    
    try:
        # Handle orphan case - just rename
        if is_orphan:
            shutil.move(duplicate, original)
            print(f"  ✅ Renamed orphan to original")
            return True, "Renamed orphan"
        
        if dup_type == 'directory':
            success, msg = merge_directories(original, duplicate)
            if success:
                shutil.rmtree(duplicate)
        else:
            ext = dup_info.get('ext', '')
            if ext == '.json':
                success, msg = merge_json_files(original, duplicate)
            elif ext in ['.md', '.txt', '.js', '.py', '.html', '.css']:
                success, msg = merge_text_files(original, duplicate)
            else:
                # For other files, keep newer
                orig_mtime = os.path.getmtime(original)
                dup_mtime = os.path.getmtime(duplicate)
                if dup_mtime > orig_mtime:
                    shutil.copy2(duplicate, original)
                    msg = "Replaced with newer duplicate"
                else:
                    msg = "Kept original (newer)"
                success = True
            
            if success:
                os.remove(duplicate)
        
        print(f"  ✅ {msg}")
        return True, msg
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, str(e)

def interactive_merge(dup_info):
    """Interactively guide user through merge."""
    dup_type = dup_info['type']
    original = dup_info['original']
    duplicate = dup_info['duplicate']
    
    print(f"\n{'='*60}")
    print(f"DUPLICATE FOUND: {os.path.basename(duplicate)}")
    print(f"  Type: {dup_type}")
    print(f"  Original: {original}")
    print(f"  Duplicate: {duplicate}")
    
    if dup_type == 'file':
        # Show diff for text files
        ext = dup_info.get('ext', '')
        if ext in ['.json', '.md', '.txt', '.js', '.py']:
            print("\n--- Comparing content ---")
            try:
                with open(original, 'r') as f:
                    orig_size = len(f.read())
                with open(duplicate, 'r') as f:
                    dup_size = len(f.read())
                print(f"  Original size: {orig_size} bytes")
                print(f"  Duplicate size: {dup_size} bytes")
            except:
                pass
    
    print("\nOptions:")
    print("  [m] Merge (combine content)")
    print("  [o] Keep original only (delete duplicate)")
    print("  [d] Keep duplicate only (replace original)")
    print("  [s] Skip (do nothing)")
    print("  [q] Quit")
    
    choice = input("\nChoice: ").strip().lower()
    
    if choice == 'm':
        return auto_merge(dup_info)
    elif choice == 'o':
        os.remove(duplicate) if dup_type == 'file' else shutil.rmtree(duplicate)
        print("  ✅ Deleted duplicate")
        return True, "Kept original"
    elif choice == 'd':
        if dup_type == 'file':
            shutil.copy2(duplicate, original)
            os.remove(duplicate)
        else:
            shutil.rmtree(original)
            shutil.move(duplicate, original)
        print("  ✅ Replaced with duplicate")
        return True, "Replaced with duplicate"
    elif choice == 's':
        print("  ⏭️ Skipped")
        return False, "Skipped"
    elif choice == 'q':
        sys.exit(0)
    else:
        print("  ❓ Invalid choice, skipping")
        return False, "Invalid choice"

def main():
    parser = argparse.ArgumentParser(description='Merge duplicate files in RAPPverse')
    parser.add_argument('--scan', action='store_true', help='List all duplicates')
    parser.add_argument('--auto', action='store_true', help='Auto-merge all duplicates')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive merge')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be merged')
    parser.add_argument('--path', default='.', help='Root path to scan')
    args = parser.parse_args()
    
    root_path = os.path.abspath(args.path)
    print(f"🔍 Scanning for duplicates in: {root_path}")
    
    duplicates = find_duplicates(root_path)
    
    if not duplicates:
        print("✨ No duplicates found!")
        return
    
    print(f"\n📋 Found {len(duplicates)} duplicates:")
    
    if args.scan or (not args.auto and not args.interactive):
        orphan_count = sum(1 for d in duplicates if d.get('orphan', False))
        merge_count = len(duplicates) - orphan_count
        
        for dup in duplicates:
            rel_dup = os.path.relpath(dup['duplicate'], root_path)
            rel_orig = os.path.relpath(dup['original'], root_path)
            status = "ORPHAN - will rename" if dup.get('orphan') else "will merge"
            print(f"  [{dup['type'][0].upper()}] {rel_dup}")
            print(f"      → {rel_orig} ({status})")
        
        print(f"\n📊 {merge_count} to merge, {orphan_count} orphans to rename")
        print(f"Run with --auto to process all, or --interactive for guided mode")
        return
    
    merged = 0
    failed = 0
    
    for dup in duplicates:
        if args.auto:
            success, _ = auto_merge(dup, dry_run=args.dry_run)
        else:
            success, _ = interactive_merge(dup)
        
        if success:
            merged += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Merged: {merged}")
    print(f"❌ Failed/Skipped: {failed}")
    
    # Refresh VS Code to show changes
    if merged > 0 and not args.dry_run:
        try:
            import subprocess
            subprocess.run(['code', '--reuse-window', root_path], 
                         capture_output=True, timeout=5)
            print("🔄 Refreshed VS Code")
        except:
            pass

if __name__ == '__main__':
    main()
