#!/usr/bin/env python3
"""
Debug Supabase Connection and Tables
"""

import sys
import os
sys.path.append('.')

def debug_supabase():
    """Debug Supabase connection and table queries"""
    print("🔍 Supabase Debug Tool")
    print("=" * 40)

    try:
        from src.core.supabase_manager import supabase_manager
        print("✅ Supabase manager imported")

        # Test connection
        connected = supabase_manager.check_connection()
        print(f"Connection status: {'✅ Connected' if connected else '❌ Failed'}")

        if connected:
            # Test getting installers
            installers = supabase_manager.get_installers()
            print(f"Installers found: {len(installers)}")
            print(f"Installer list: {installers}")

            if not installers:
                print("❌ No installers returned - table might be empty or query failed")
                # Try manual query
                print("\n🔍 Trying manual query...")
                try:
                    import requests
                    headers = supabase_manager._headers()
                    url = supabase_manager._url("authorized_persons")
                    print(f"Querying URL: {url}")
                    print(f"Headers: apikey=***, Authorization=Bearer ***")

                    params = {"select": "names", "order": "names.asc"}
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    print(f"Response status: {response.status_code}")
                    print(f"Response text: {response.text[:200]}...")

                    if response.status_code == 200:
                        data = response.json()
                        print(f"Raw data: {data}")
                        names = [row.get("names") for row in data if row.get("names")]
                        print(f"Extracted names: {names}")
                    else:
                        print(f"❌ Query failed with status {response.status_code}")

                except Exception as e:
                    print(f"❌ Manual query error: {e}")
            else:
                print("✅ Installers found successfully")

        else:
            print("❌ Cannot test queries - no connection")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_supabase()