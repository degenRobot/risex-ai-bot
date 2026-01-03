#!/usr/bin/env python3
"""Test API pagination and account_id inclusion."""

import json

import requests

BASE_URL = "http://localhost:8000"


def test_paginated_profiles():
    """Test the paginated profiles endpoint."""
    print("Testing paginated profiles endpoint...")
    
    # Test default pagination (page 1, limit 20)
    response = requests.get(f"{BASE_URL}/api/profiles")
    assert response.status_code == 200
    
    data = response.json()
    print("\nDefault pagination response:")
    print(json.dumps(data, indent=2))
    
    assert "profiles" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "has_more" in data
    
    # Check profiles have account_id
    if data["profiles"]:
        profile = data["profiles"][0]
        assert "account_id" in profile
        assert "handle" in profile
        assert "name" in profile
        print(f"\n✅ First profile has account_id: {profile['account_id']}")
    
    # Test custom pagination
    response = requests.get(f"{BASE_URL}/api/profiles?page=2&limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 2
    assert data["limit"] == 5
    assert len(data["profiles"]) <= 5
    print(f"\n✅ Custom pagination works: page={data['page']}, limit={data['limit']}")


def test_all_profiles():
    """Test the backward compatible all profiles endpoint."""
    print("\n\nTesting all profiles endpoint (backward compatibility)...")
    
    response = requests.get(f"{BASE_URL}/api/profiles/all")
    assert response.status_code == 200
    
    profiles = response.json()
    assert isinstance(profiles, list)
    
    if profiles:
        profile = profiles[0]
        assert "account_id" in profile
        print(f"✅ All profiles endpoint works, found {len(profiles)} profiles")


def test_profile_detail():
    """Test that profile detail includes account_id."""
    print("\n\nTesting profile detail endpoint...")
    
    # First get a handle from the list
    response = requests.get(f"{BASE_URL}/api/profiles/all")
    profiles = response.json()
    
    if not profiles:
        print("No profiles found, skipping detail test")
        return
    
    handle = profiles[0]["handle"]
    account_id = profiles[0]["account_id"]
    
    # Get profile detail
    response = requests.get(f"{BASE_URL}/api/profiles/{handle}")
    assert response.status_code == 200
    
    detail = response.json()
    assert "account_id" in detail
    assert detail["account_id"] == account_id
    assert detail["handle"] == handle
    
    print(f"✅ Profile detail includes account_id: {detail['account_id']}")


def main():
    """Run all tests."""
    print("🧪 Testing API pagination and account_id inclusion")
    print("=" * 50)
    
    try:
        test_paginated_profiles()
        test_all_profiles()
        test_profile_detail()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()