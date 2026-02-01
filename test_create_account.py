#!/usr/bin/env python3
"""
Test Create Account Window
Simple test to check if the registration window can open
"""

import sys
import os
sys.path.append('.')

def test_create_account_window():
    """Test if CreateAccountWindow can be imported and instantiated"""
    print("🔍 Testing Create Account Window...")
    print("=" * 40)

    try:
        # Test import
        from src.ui.views.onboarding.create_account_stepper import CreateAccountWindow
        print("✅ CreateAccountWindow import: SUCCESS")

        # Test instantiation (without showing GUI)
        window = CreateAccountWindow()
        print("✅ CreateAccountWindow instantiation: SUCCESS")

        # Check if it has the required methods
        if hasattr(window, 'account_created'):
            print("✅ account_created signal: PRESENT")
        else:
            print("❌ account_created signal: MISSING")

        if hasattr(window, 'init_step1'):
            print("✅ Step 1 initialization: PRESENT")
        else:
            print("❌ Step 1 initialization: MISSING")

        if hasattr(window, 'go_next'):
            print("✅ Navigation methods: PRESENT")
        else:
            print("❌ Navigation methods: MISSING")

        print("\n🎯 Create Account Window: READY")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Instantiation error: {e}")
        return False

def test_login_window():
    """Test if LoginWindow can be imported and instantiated"""
    print("\n🔍 Testing Login Window...")
    print("=" * 40)

    try:
        # Test import
        from src.ui.views.onboarding.login_window import LoginWindow
        print("✅ LoginWindow import: SUCCESS")

        # Test instantiation (without showing GUI)
        window = LoginWindow()
        print("✅ LoginWindow instantiation: SUCCESS")

        # Check if it has the required methods
        if hasattr(window, 'login_success'):
            print("✅ login_success signal: PRESENT")
        else:
            print("❌ login_success signal: MISSING")

        print("\n🎯 Login Window: READY")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Instantiation error: {e}")
        return False

def main():
    print("🧪 POS Onboarding Windows Test")
    print("=" * 50)
    print("Testing if registration and login windows can be loaded\n")

    create_ok = test_create_account_window()
    login_ok = test_login_window()

    print("\n" + "=" * 50)
    if create_ok and login_ok:
        print("🟢 ONBOARDING WINDOWS: READY")
        print("   The registration flow should work correctly")
        print("   Run the POS application to test the complete flow")
    else:
        print("🔴 ONBOARDING WINDOWS: ISSUES FOUND")
        print("   Fix the errors above before running the app")

    return create_ok and login_ok

if __name__ == "__main__":
    main()