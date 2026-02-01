#!/usr/bin/env python3
"""
Basic Test - Check if the POS system can start and show the registration issue
"""

import sys
import os
sys.path.append('.')

def test_basic_import():
    """Test basic imports without running the full app"""
    print("🔍 BASIC POS SYSTEM TEST")
    print("=" * 40)

    try:
        # Test core imports
        from src.core.local_config import local_config
        print("✅ Local config imported")

        is_registered = local_config.is_registered()
        print(f"Account registered: {is_registered}")

        # Test UI imports
        from src.ui.views.onboarding.create_account_stepper import CreateAccountWindow
        print("✅ Create Account Window imported")

        from src.ui.views.onboarding.login_window import LoginWindow
        print("✅ Login Window imported")

        from src.ui.views.onboarding.connectivity_gate import ConnectivityGateWindow
        print("✅ Connectivity Gate imported")

        print("\n🎯 All components can be imported successfully")
        print("The issue is likely with the Supabase connection or table access")

        print("\n📋 TROUBLESHOOTING STEPS:")
        print("1. Check if authorized_persons table exists in Supabase")
        print("2. Verify the table has columns: id, created_at, names, passwords")
        print("3. Check Row Level Security (RLS) settings")
        print("4. Ensure API key has read permissions")
        print("5. Try running the app and check console output for detailed error messages")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_import()