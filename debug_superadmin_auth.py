#!/usr/bin/env python3
"""
Debug script to check superadmin credentials in Supabase
"""
import os
import requests
from dotenv import load_dotenv

# Load credentials
env_path = os.path.join(os.path.dirname(__file__), "credentials", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

print("=" * 60)
print("SUPERADMIN AUTHENTICATION DEBUGGER")
print("=" * 60)
print(f"\nSupabase URL: {SUPABASE_URL}")
print(f"Service Key: {SERVICE_KEY[:10]}...{SERVICE_KEY[-5:] if SERVICE_KEY else 'MISSING'}")
print()

def check_authorized_persons():
    """Check all entries in authorized_persons table"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        params = {"select": "id,names,passwords,role,created_at"}
        
        print("📋 Fetching authorized_persons table...")
        r = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"Status Code: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\n✅ Found {len(data)} authorized person(s):\n")
            
            for idx, person in enumerate(data, 1):
                print(f"{idx}. Username: {person.get('names')}")
                print(f"   Password: {person.get('passwords')}")
                print(f"   Role: {person.get('role', 'N/A')}")
                print(f"   Created: {person.get('created_at', 'N/A')}")
                print()
            
            return data
        else:
            print(f"❌ Error: {r.status_code}")
            print(f"Response: {r.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_verification(username, password):
    """Test the verify_installer method"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        params = {
            "names": f"eq.{username.strip()}",
            "passwords": f"eq.{password.strip()}",
            "select": "id"
        }
        
        print(f"\n🔍 Testing verification for: {username}")
        print(f"   Password: {password}")
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            if len(data) > 0:
                print(f"   ✅ AUTHENTICATION SUCCESSFUL")
                return True
            else:
                print(f"   ❌ AUTHENTICATION FAILED - No matching record")
                return False
        else:
            print(f"   ❌ ERROR: {r.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def add_superadmin(username, password):
    """Add or update superadmin credentials"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        payload = {
            "names": username.strip(),
            "passwords": password.strip(),
            "role": "superadmin"
        }
        
        # Try upsert
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons?on_conflict=names"
        
        print(f"\n📝 Adding/Updating superadmin...")
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if r.status_code in (200, 201, 204):
            print(f"   ✅ SUCCESS - Superadmin credentials saved")
            return True
        else:
            print(f"   ❌ ERROR: {r.status_code}")
            print(f"   Response: {r.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

# Main execution
if __name__ == "__main__":
    # Check current state
    persons = check_authorized_persons()
    
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Test superadmin authentication")
        print("2. Add/Update superadmin credentials")
        print("3. Refresh table view")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            username = input("Enter username to test (default: superadmin): ").strip() or "superadmin"
            password = input("Enter password to test: ").strip()
            if password:
                test_verification(username, password)
        
        elif choice == "2":
            username = input("Enter username (default: superadmin): ").strip() or "superadmin"
            password = input("Enter new password: ").strip()
            if password:
                if add_superadmin(username, password):
                    print("\n✅ Now testing the new credentials...")
                    test_verification(username, password)
        
        elif choice == "3":
            persons = check_authorized_persons()
        
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")
