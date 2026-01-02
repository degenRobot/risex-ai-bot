#!/usr/bin/env python3
"""Repair corrupted JSON data files in production."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage import JSONStorage


def main():
    """Check and repair all data files."""
    print("🔧 DATA FILE REPAIR UTILITY")
    print("=" * 50)
    
    storage = JSONStorage()
    
    print("\nChecking all data files...")
    results = storage.repair_all_data_files()
    
    print("\nResults:")
    print("-" * 50)
    
    repaired_count = 0
    for filename, status in sorted(results.items()):
        icon = "✅" if status == "valid" else "🔧"
        print(f"{icon} {filename}: {status}")
        if status == "repaired":
            repaired_count += 1
    
    print("-" * 50)
    print(f"\nTotal files checked: {len(results)}")
    print(f"Files repaired: {repaired_count}")
    
    if repaired_count > 0:
        print("\n⚠️  IMPORTANT: Corrupted files have been backed up with .backup extension")
        print("   and reset to empty JSON objects. You may need to restore data manually.")
    else:
        print("\n✅ All files are valid!")


if __name__ == "__main__":
    main()