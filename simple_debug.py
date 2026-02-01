#!/usr/bin/env python3
"""
Simple Debug Script - Test Supabase Manager without external dependencies
"""

import sys
import os
sys.path.append('.')

def debug_supabase_manager():
    """Debug the Supabase manager directly"""
    print("🔍 SIMPLE SUPABASE DEBUG")
    print("=" * 40)

    try:
        from src.core.supabase_manager import supabase_manager

        print("✅ Supabase manager imported")

        # Check configuration
        print(f"URL: {supabase_manager.url}")
        print(f"Key present: {'✅ Yes' if supabase_manager.key else '❌ No'}")
        print(f"Key length: {len(supabase_manager.key) if supabase_manager.key else 0}")

        # Test table URLs
        users_url = supabase_manager._url(supabase_manager.USERS_TABLE)
        print(f"Users table URL: {users_url}")

        # Test headers
        headers = supabase_manager._headers()
        print(f"Headers: apikey=***, Authorization=Bearer ***")

        # Test connection check
        print("\nTesting connection...")
        connected = supabase_manager.check_connection()
        print(f"Connection result: {'✅ Connected' if connected else '❌ Failed'}")

        # Test get_installers
        print("\nTesting get_installers...")
        installers = supabase_manager.get_installers()
        print(f"Installers returned: {installers}")
        print(f"Count: {len(installers)}")

        if not installers:
            print("❌ NO INSTALLERS FOUND - This is the problem!")
            print("\nPossible causes:")
            print("1. Table 'authorized_persons' is actually empty")
            print("2. Column name is not 'names'")
            print("3. API key has insufficient permissions")
            print("4. Row Level Security (RLS) blocking access")
            print("5. Wrong table name")
        else:
            print("✅ Installers found - registration should work")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_supabase_manager()