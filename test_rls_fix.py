#!/usr/bin/env python3
"""
Test if RLS fix worked for authorized_persons table
"""

import sys
import os
sys.path.append('.')

def test_rls_fix():
    """Test if the RLS fix resolved the authorized_persons issue"""
    print("🧪 TESTING RLS FIX")
    print("=" * 40)

    try:
        from src.core.supabase_manager import supabase_manager

        print("✅ Supabase manager loaded")

        # Test connection
        connected = supabase_manager.check_connection()
        if not connected:
            print("❌ Cannot connect to Supabase")
            return False

        print("✅ Connected to Supabase")

        # Test get_installers
        print("\n🔍 Testing authorized_persons table access...")
        installers = supabase_manager.get_installers()

        if not installers:
            print("❌ STILL EMPTY: authorized_persons table not accessible")
            print("\n🔧 POSSIBLE FIXES:")
            print("1. Check if you ran the RLS fix SQL")
            print("2. Verify service role key is being used")
            print("3. Check Supabase dashboard for RLS settings")
            return False

        print(f"✅ SUCCESS: Found {len(installers)} installers: {installers}")

        # Test verification with first installer
        if installers:
            test_user = installers[0]
            print(f"\n🔐 Testing authentication for: {test_user}")

            # You would need to provide the password here
            password = input(f"Enter password for {test_user} (or press Enter to skip): ").strip()

            if password:
                result = supabase_manager.verify_installer(test_user, password)
                print(f"Authentication: {'✅ SUCCESS' if result else '❌ FAILED'}")
            else:
                print("Skipped authentication test")

        print("\n🎉 RLS ISSUE FIXED!")
        print("Registration should now work properly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_rls_fix()