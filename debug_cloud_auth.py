#!/usr/bin/env python3
"""
Debug Cloud Authorization - Test authorized_persons table
"""

import sys
import os
sys.path.append('.')

def debug_cloud_auth():
    """Debug the authorized_persons table in Supabase"""
    print("🔍 Testing Cloud Authorization Table")
    print("=" * 50)

    try:
        from src.core.supabase_manager import supabase_manager

        # Test connection
        connected = supabase_manager.check_connection()
        print(f"Cloud Connection: {'✅ Connected' if connected else '❌ Failed'}")

        if not connected:
            print("❌ Cannot proceed without cloud connection")
            return

        # Test getting installers
        print("\n📋 Fetching authorized installers...")
        installers = supabase_manager.get_installers()

        print(f"Number of installers found: {len(installers)}")
        if installers:
            print("Installers:")
            for i, installer in enumerate(installers, 1):
                print(f"  {i}. {installer}")
        else:
            print("❌ No installers found in authorized_persons table")

        # Test verification with first installer if available
        if installers:
            test_user = installers[0]
            print(f"\n🔐 Testing authentication for user: {test_user}")

            # Ask for password
            password = input(f"Enter password for {test_user}: ").strip()
            if password:
                result = supabase_manager.verify_installer(test_user, password)
                print(f"Authentication result: {'✅ SUCCESS' if result else '❌ FAILED'}")
            else:
                print("No password provided - skipping auth test")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_cloud_auth()