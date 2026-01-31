#!/usr/bin/env python3
"""
Molt Merger - Handles iCloud/sync duplicate files ("molts") as a feature.

Molts are files created by sync systems (iCloud, Dropbox, etc.) when conflicts occur.
They follow patterns like "filename 2.ext", "filename 3.ext", etc.

This script treats molts as a local caching/versioning mechanism:
1. Detects all molt files in the repo
2. Compares them with their originals
3. Merges differences or flags conflicts
4. Cleans up after successful merge

Usage:
    python scripts/molt_merger.py              # Scan and report molts
    python scripts/molt_merger.py --merge      # Auto-merge identical molts
    python scripts/molt_merger.py --diff       # Show differences in changed molts
    python scripts/molt_merger.py --adopt N    # Adopt molt version N as the new original
    python scripts/molt_merger.py --clean      # Remove molts after review
"""

import os
import re
import sys
import json
import hashlib
import argparse
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Molt detection pattern: "filename 2.ext", "filename 3.ext", etc.
MOLT_PATTERN = re.compile(r'^(.+) (\d+)(\.[^.]+)$')

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.local_storage'}


def find_molts(root_dir: str = '.') -> Dict[str, List[dict]]:
    """
    Find all molt files and group them with their originals.

    Returns:
        Dict mapping original file path to list of molt info dicts
    """
    molts = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            match = MOLT_PATTERN.match(filename)
            if match:
                base_name = match.group(1)
                molt_num = int(match.group(2))
                extension = match.group(3)

                original_name = f"{base_name}{extension}"
                original_path = os.path.join(dirpath, original_name)
                molt_path = os.path.join(dirpath, filename)

                if original_path not in molts:
                    molts[original_path] = []

                molts[original_path].append({
                    'path': molt_path,
                    'number': molt_num,
                    'exists_original': os.path.exists(original_path),
                    'size': os.path.getsize(molt_path) if os.path.exists(molt_path) else 0,
                    'mtime': os.path.getmtime(molt_path) if os.path.exists(molt_path) else 0
                })

    # Sort molts by number for each original
    for original in molts:
        molts[original].sort(key=lambda x: x['number'])

    return molts


def file_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file."""
    if not os.path.exists(filepath):
        return ''
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def compare_files(file1: str, file2: str) -> Tuple[bool, Optional[str]]:
    """
    Compare two files.

    Returns:
        (are_identical, diff_summary)
    """
    if not os.path.exists(file1) or not os.path.exists(file2):
        return False, "One or both files don't exist"

    hash1 = file_hash(file1)
    hash2 = file_hash(file2)

    if hash1 == hash2:
        return True, None

    # Generate diff for text files
    try:
        with open(file1, 'r', encoding='utf-8') as f:
            content1 = f.readlines()
        with open(file2, 'r', encoding='utf-8') as f:
            content2 = f.readlines()

        diff = list(difflib.unified_diff(content1, content2,
                                          fromfile=file1, tofile=file2, lineterm=''))
        if diff:
            return False, '\n'.join(diff[:50])  # First 50 lines of diff
    except (UnicodeDecodeError, IOError):
        return False, "Binary files differ"

    return False, "Files differ (no readable diff)"


def analyze_molts(molts: Dict[str, List[dict]]) -> dict:
    """
    Analyze molt status for all files.

    Returns summary with categories:
    - identical: Molts that match original (safe to delete)
    - newer: Molts that are newer than original
    - different: Molts that differ from original
    - orphaned: Molts with no original file
    """
    analysis = {
        'identical': [],
        'newer': [],
        'different': [],
        'orphaned': [],
        'total_molt_count': 0
    }

    for original_path, molt_list in molts.items():
        analysis['total_molt_count'] += len(molt_list)

        for molt in molt_list:
            molt_path = molt['path']

            if not molt['exists_original']:
                analysis['orphaned'].append({
                    'original': original_path,
                    'molt': molt_path,
                    'number': molt['number']
                })
                continue

            identical, diff = compare_files(original_path, molt_path)

            if identical:
                analysis['identical'].append({
                    'original': original_path,
                    'molt': molt_path,
                    'number': molt['number']
                })
            else:
                original_mtime = os.path.getmtime(original_path)
                molt_mtime = molt['mtime']

                entry = {
                    'original': original_path,
                    'molt': molt_path,
                    'number': molt['number'],
                    'diff_preview': diff,
                    'molt_newer': molt_mtime > original_mtime
                }

                if molt_mtime > original_mtime:
                    analysis['newer'].append(entry)
                else:
                    analysis['different'].append(entry)

    return analysis


def print_report(analysis: dict, verbose: bool = False):
    """Print a summary report of molt analysis."""

    print("\n" + "=" * 60)
    print("MOLT ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nTotal molts found: {analysis['total_molt_count']}")
    print(f"  - Identical to original: {len(analysis['identical'])} (safe to delete)")
    print(f"  - Newer than original:   {len(analysis['newer'])} (consider adopting)")
    print(f"  - Different from orig:   {len(analysis['different'])} (review needed)")
    print(f"  - Orphaned (no orig):    {len(analysis['orphaned'])} (may be the real file)")

    if verbose:
        if analysis['newer']:
            print("\n--- NEWER MOLTS (molt is more recent) ---")
            for item in analysis['newer']:
                print(f"\n  Original: {item['original']}")
                print(f"  Molt:     {item['molt']}")
                if item.get('diff_preview'):
                    print(f"  Diff preview:\n    {item['diff_preview'][:200]}...")

        if analysis['orphaned']:
            print("\n--- ORPHANED MOLTS (no original found) ---")
            for item in analysis['orphaned']:
                print(f"  Molt: {item['molt']}")
                print(f"  Expected original: {item['original']}")

    print("\n" + "=" * 60)


def merge_identical(analysis: dict, dry_run: bool = True) -> int:
    """Delete molts that are identical to their originals."""
    count = 0
    for item in analysis['identical']:
        if dry_run:
            print(f"Would delete: {item['molt']}")
        else:
            os.remove(item['molt'])
            print(f"Deleted: {item['molt']}")
        count += 1
    return count


def adopt_molt(molt_path: str, original_path: str, dry_run: bool = True) -> bool:
    """Replace original with molt version."""
    if not os.path.exists(molt_path):
        print(f"Error: Molt not found: {molt_path}")
        return False

    if dry_run:
        print(f"Would replace {original_path} with {molt_path}")
    else:
        # Backup original if it exists
        if os.path.exists(original_path):
            backup_path = f"{original_path}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(original_path, backup_path)
            print(f"Backed up original to: {backup_path}")

        os.rename(molt_path, original_path)
        print(f"Adopted molt as new original: {original_path}")

    return True


def clean_all_molts(molts: Dict[str, List[dict]], dry_run: bool = True) -> int:
    """Remove all molt files (use after review)."""
    count = 0
    for original_path, molt_list in molts.items():
        for molt in molt_list:
            if dry_run:
                print(f"Would delete: {molt['path']}")
            else:
                if os.path.exists(molt['path']):
                    os.remove(molt['path'])
                    print(f"Deleted: {molt['path']}")
            count += 1
    return count


def show_diff(original: str, molt: str):
    """Show full diff between original and molt."""
    if not os.path.exists(original):
        print(f"Original not found: {original}")
        return
    if not os.path.exists(molt):
        print(f"Molt not found: {molt}")
        return

    try:
        with open(original, 'r', encoding='utf-8') as f:
            content1 = f.readlines()
        with open(molt, 'r', encoding='utf-8') as f:
            content2 = f.readlines()

        diff = difflib.unified_diff(content1, content2,
                                     fromfile=f"original: {original}",
                                     tofile=f"molt: {molt}")
        print('\n'.join(diff))
    except UnicodeDecodeError:
        print("Binary files - cannot show diff")


def main():
    parser = argparse.ArgumentParser(
        description="Molt Merger - Handle sync duplicates as a feature",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/molt_merger.py                    # Scan and report
  python scripts/molt_merger.py -v                 # Verbose report
  python scripts/molt_merger.py --merge            # Delete identical molts
  python scripts/molt_merger.py --merge --execute  # Actually delete
  python scripts/molt_merger.py --diff file.py     # Show diff for specific file
  python scripts/molt_merger.py --adopt "file 3.py" # Adopt molt version
  python scripts/molt_merger.py --clean            # Remove all molts
        """
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed information')
    parser.add_argument('--merge', action='store_true',
                        help='Delete molts identical to originals')
    parser.add_argument('--diff', metavar='FILE',
                        help='Show diff for a specific file and its molts')
    parser.add_argument('--adopt', metavar='MOLT_PATH',
                        help='Adopt a molt as the new original')
    parser.add_argument('--clean', action='store_true',
                        help='Remove all molts (after review)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform changes (default is dry-run)')
    parser.add_argument('--json', action='store_true',
                        help='Output analysis as JSON')

    args = parser.parse_args()

    # Find all molts
    molts = find_molts('.')

    if not molts:
        print("No molts found.")
        return 0

    # Handle specific operations
    if args.diff:
        # Find molts for the specified file
        target = args.diff
        for original, molt_list in molts.items():
            if target in original or any(target in m['path'] for m in molt_list):
                print(f"\nComparing: {original}")
                for molt in molt_list:
                    print(f"\n--- Molt {molt['number']}: {molt['path']} ---")
                    show_diff(original, molt['path'])
                return 0
        print(f"No molts found for: {target}")
        return 1

    if args.adopt:
        # Find the molt and its original
        for original, molt_list in molts.items():
            for molt in molt_list:
                if args.adopt in molt['path']:
                    return 0 if adopt_molt(molt['path'], original, not args.execute) else 1
        print(f"Molt not found: {args.adopt}")
        return 1

    # Analyze molts
    analysis = analyze_molts(molts)

    if args.json:
        # Remove non-serializable parts
        for category in ['identical', 'newer', 'different', 'orphaned']:
            for item in analysis[category]:
                if 'diff_preview' in item:
                    item['diff_preview'] = item['diff_preview'][:500] if item['diff_preview'] else None
        print(json.dumps(analysis, indent=2))
        return 0

    # Print report
    print_report(analysis, args.verbose)

    # Handle merge
    if args.merge:
        dry_run = not args.execute
        if dry_run:
            print("\n[DRY RUN] Would delete these identical molts:")
        else:
            print("\nDeleting identical molts:")
        count = merge_identical(analysis, dry_run)
        print(f"\n{'Would delete' if dry_run else 'Deleted'} {count} identical molts")
        if dry_run:
            print("Run with --execute to actually delete")

    # Handle clean
    if args.clean:
        dry_run = not args.execute
        if dry_run:
            print("\n[DRY RUN] Would delete ALL molts:")
        else:
            print("\nDeleting ALL molts:")
        count = clean_all_molts(molts, dry_run)
        print(f"\n{'Would delete' if dry_run else 'Deleted'} {count} molts")
        if dry_run:
            print("Run with --execute to actually delete")

    # Suggest next steps
    if not args.merge and not args.clean:
        print("\nNext steps:")
        if analysis['identical']:
            print(f"  - Run with --merge to delete {len(analysis['identical'])} identical molts")
        if analysis['newer']:
            print(f"  - Review {len(analysis['newer'])} newer molts (may want to --adopt)")
        if analysis['orphaned']:
            print(f"  - Review {len(analysis['orphaned'])} orphaned molts")
        print("  - Run with --clean --execute to remove all molts after review")

    return 0


if __name__ == '__main__':
    sys.exit(main())
