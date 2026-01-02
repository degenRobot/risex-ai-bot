#!/usr/bin/env python3
"""Test storage resilience to corrupted data files."""

import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.storage import JSONStorage


def test_corrupted_json_recovery():
    """Test that storage can recover from corrupted JSON files."""
    
    print("🧪 Testing Storage Resilience")
    print("=" * 50)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize storage with temp directory
        storage = JSONStorage(data_dir=temp_dir)
        
        # Test 1: Valid JSON
        print("\n1. Testing valid JSON...")
        test_data = {"test": "data", "count": 123}
        storage._save_json(storage.accounts_file, test_data)
        loaded = storage._load_json(storage.accounts_file)
        assert loaded == test_data
        print("✅ Valid JSON loaded correctly")
        
        # Test 2: Corrupted JSON
        print("\n2. Testing corrupted JSON recovery...")
        with open(storage.pending_actions_file, 'w') as f:
            f.write('{"broken": json with invalid syntax}')
        
        # Should recover and return empty dict
        loaded = storage._load_json(storage.pending_actions_file)
        assert loaded == {}
        print("✅ Corrupted JSON recovered to empty dict")
        
        # Check backup was created
        backups = list(Path(temp_dir).glob("*.backup.*"))
        assert len(backups) == 1
        print(f"✅ Backup created: {backups[0].name}")
        
        # Test 3: Missing file
        print("\n3. Testing missing file...")
        missing_path = Path(temp_dir) / "missing.json"
        loaded = storage._load_json(missing_path)
        assert loaded == {}
        print("✅ Missing file returns empty dict")
        
        # Test 4: API methods with corrupted data
        print("\n4. Testing API methods with recovery...")
        
        # Corrupt the accounts file
        with open(storage.accounts_file, 'w') as f:
            f.write('{"account1": {"invalid": json},}')
        
        # Should handle gracefully
        accounts = storage.list_accounts()
        assert accounts == []
        print("✅ list_accounts() handled corrupted data")
        
        # Test repair_all_data_files
        print("\n5. Testing repair_all_data_files...")
        
        # Create some corrupted files
        corrupted_files = [
            storage.trades_file,
            storage.decisions_file,
            storage.sessions_file
        ]
        
        for file_path in corrupted_files:
            with open(file_path, 'w') as f:
                f.write('{"bad": json with, trailing comma,}')
        
        # Repair all files
        results = storage.repair_all_data_files()
        
        # Check results
        repaired_count = sum(1 for status in results.values() if status == "repaired")
        print(f"✅ Repaired {repaired_count} files")
        
        # Verify all files are now valid
        for file_path in corrupted_files:
            assert storage.validate_json_file(file_path)
        print("✅ All files are now valid JSON")
        
        print("\n" + "=" * 50)
        print("✅ All resilience tests passed!")


if __name__ == "__main__":
    test_corrupted_json_recovery()