#!/usr/bin/env python3
"""
Test Registration Flow
Run this to debug the account creation and login process
"""

import sys
import os
sys.path.append('.')

from src.core.supabase_manager import supabase_manager
from src.core.local_config import local_config

def test_supabase_connection():
    """Test basic Supabase connectivity"""
    print("🔍 Testing Supabase Connection...")
    print("=" * 40)

    try:
        connected = supabase_manager.check_connection()
        if connected:
            print("✅ Supabase connection: WORKING")
        else:
            print("❌ Supabase connection: FAILED")
            print("   This will prevent registration from working")
        return connected
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_installer_verification():
    """Test if we can verify installers"""
    print("\n🔍 Testing Installer Verification...")
    print("=" * 40)

    try:
        installers = supabase_manager.get_installers()
        print(f"Available installers: {installers}")

        if not installers or installers == ["admin"]:
            print("❌ No valid installers found in database")
            print("   Registration will fail without valid installer credentials")
            return False

        print("✅ Installer list retrieved successfully")
        return True
    except Exception as e:
        print(f"❌ Installer verification error: {e}")
        return False

def test_local_config():
    """Test local configuration"""
    print("\n🔍 Testing Local Configuration...")
    print("=" * 40)

    try:
        is_registered = local_config.is_registered()
        login_mode = local_config.get("login_mode", "NOT SET")
        company_name = local_config.get("company_name", "NOT SET")

        print(f"Account registered: {is_registered}")
        print(f"Login mode: {login_mode}")
        print(f"Company name: {company_name}")

        if is_registered:
            print("✅ User is already registered - app should start directly")
        else:
            print("❌ User not registered - registration flow should start")

        return True
    except Exception as e:
        print(f"❌ Local config error: {e}")
        return False

def simulate_registration_flow():
    """Simulate what happens during registration"""
    print("\n🔍 Simulating Registration Flow...")
    print("=" * 40)

    # Check connectivity
    connected = test_supabase_connection()
    if not connected:
        print("❌ Cannot proceed with registration - no internet/Supabase")
        return False

    # Check installers
    has_installers = test_installer_verification()
    if not has_installers:
        print("❌ Cannot proceed with registration - no installers")
        return False

    # Check local config
    config_ok = test_local_config()

    print("\n📋 REGISTRATION FLOW SUMMARY:")
    print("=" * 40)
    print("1. ✅ Internet connectivity: OK" if connected else "1. ❌ Internet connectivity: FAILED")
    print("2. ✅ Installer verification: OK" if has_installers else "2. ❌ Installer verification: FAILED")
    print("3. ✅ Local configuration: OK" if config_ok else "3. ❌ Local configuration: FAILED")

    if connected and has_installers and config_ok:
        print("\n🎯 REGISTRATION SHOULD WORK")
        print("   If registration still fails, check:")
        print("   - Installer username/password are correct")
        print("   - Supabase table permissions")
        print("   - Network firewall blocking requests")
    else:
        print("\n❌ REGISTRATION WILL FAIL")
        print("   Fix the failed checks above first")

    return connected and has_installers and config_ok

def main():
    print("🧪 POS System Registration Flow Test")
    print("=" * 50)
    print("This script tests the complete registration flow")
    print("to help debug why account creation might not work.\n")

    success = simulate_registration_flow()

    print("\n" + "=" * 50)
    if success:
        print("🟢 REGISTRATION SYSTEM: READY")
        print("   Try running the POS application now")
    else:
        print("🔴 REGISTRATION SYSTEM: NEEDS FIXES")
        print("   Address the issues above before running the app")

    return success

if __name__ == "__main__":
    main()