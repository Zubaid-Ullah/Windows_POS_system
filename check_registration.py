#!/usr/bin/env python3
"""
Check registration status of the POS system
"""

import sys
import os
sys.path.append('.')

from src.core.local_config import local_config

def main():
    print("🔍 POS System Registration Check")
    print("=" * 40)

    # Check registration status
    is_registered = local_config.is_registered()
    print(f"Registered: {is_registered}")

    # Show all config data
    print("\n📋 Current Configuration:")
    print("-" * 40)

    config_keys = [
        'system_id', 'pc_name', 'account_created', 'login_mode',
        'company_name', 'phone', 'email', 'status'
    ]

    for key in config_keys:
        value = local_config.get(key, 'NOT SET')
        print(f"{key}: {value}")

    print("\n💡 Troubleshooting:")
    print("-" * 40)

    if not is_registered:
        print("❌ User is not registered - this will trigger registration flow")
        print("   After registration completes, the app should start normally")
    else:
        print("✅ User is registered - app should start directly")
        login_mode = local_config.get('login_mode')
        print(f"   Login mode: {login_mode}")
        if login_mode == 'once':
            print("   → Will start main app directly")
        else:
            print("   → Will show login window")

    print("\n🔧 If issues persist:")
    print("   1. Delete ~/.afex_pos_config.json to reset registration")
    print("   2. Check credentials/useraccount.txt for account data")
    print("   3. Run the app again to go through registration")

if __name__ == "__main__":
    main()