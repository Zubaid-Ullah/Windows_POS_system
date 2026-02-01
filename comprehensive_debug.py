#!/usr/bin/env python3
"""
Comprehensive Supabase Debug Script
Tests all aspects of the connection and data retrieval
"""

import sys
import os
import requests
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), 'credentials', '.env')
load_dotenv(dotenv_path)

def test_supabase_connection():
    """Test all aspects of Supabase connection"""
    print("🔍 COMPREHENSIVE SUPABASE DEBUG")
    print("=" * 60)

    # Configuration
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gwmtlvquhlqtkyynuexf.supabase.co").rstrip("/")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SERVICE_ROLE_KEY")

    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Key present: {'✅ Yes' if SUPABASE_KEY else '❌ No'}")
    print(f"Key starts with: {SUPABASE_KEY[:20] + '...' if SUPABASE_KEY else 'N/A'}")
    print()

    # Test basic connectivity
    print("1️⃣ Testing Basic Internet Connectivity...")
    try:
        response = requests.get("https://www.google.com", timeout=5)
        print(f"   ✅ Google reachable: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Google unreachable: {e}")
        return

    # Test Supabase endpoint
    print("\n2️⃣ Testing Supabase Endpoint...")
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/"
        print(f"   URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   ✅ Supabase reachable: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Supabase unreachable: {e}")
        return

    # Test table access
    print("\n3️⃣ Testing Table Access...")

    tables_to_test = [
        "authorized_persons",
        "installations",
        "client_name_password"
    ]

    for table in tables_to_test:
        print(f"\n   Testing table: {table}")
        try:
            headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
            url = f"{SUPABASE_URL}/rest/v1/{table}"
            params = {"select": "*", "limit": "5"}

            print(f"      URL: {url}")
            print(f"      Params: {params}")

            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"      Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Records found: {len(data) if isinstance(data, list) else 'N/A'}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"      Sample record: {data[0]}")
                elif isinstance(data, dict):
                    print(f"      Response: {data}")
            else:
                print(f"      ❌ Error: {response.text}")

        except Exception as e:
            print(f"      ❌ Exception: {e}")

    # Test specific authorized_persons query
    print("\n4️⃣ Testing authorized_persons Query...")
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        params = {"select": "names", "order": "names.asc"}

        print(f"   URL: {url}")
        print(f"   Params: {params}")

        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Raw response: {data}")
            if isinstance(data, list):
                names = [row.get("names") for row in data if row.get("names")]
                print(f"   ✅ Extracted names: {names}")
                print(f"   ✅ Count: {len(names)}")
            else:
                print(f"   ⚠️ Unexpected response format: {type(data)}")
        else:
            print(f"   ❌ Error response: {response.text}")

    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # Test with manager class
    print("\n5️⃣ Testing with SupabaseManager Class...")
    try:
        sys.path.append('.')
        from src.core.supabase_manager import supabase_manager

        print("   ✅ Manager imported")

        connection_ok = supabase_manager.check_connection()
        print(f"   Connection check: {'✅ OK' if connection_ok else '❌ Failed'}")

        installers = supabase_manager.get_installers()
        print(f"   Installers via manager: {installers}")
        print(f"   Count: {len(installers)}")

    except Exception as e:
        print(f"   ❌ Manager test failed: {e}")

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("\nIf the table shows as empty but you know it has data:")
    print("1. Check table name spelling: 'authorized_persons'")
    print("2. Check column name: 'names' (not 'name')")
    print("3. Verify API key has read permissions")
    print("4. Check Row Level Security (RLS) settings in Supabase")
    print("5. Try the query directly in Supabase SQL editor")

if __name__ == "__main__":
    test_supabase_connection()