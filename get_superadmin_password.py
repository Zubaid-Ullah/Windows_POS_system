#!/usr/bin/env python3
"""
Fetch the current superadmin password from Supabase
"""
import os
import requests
from dotenv import load_dotenv

# Load credentials
env_path = os.path.join(os.path.dirname(__file__), "credentials", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

print("=" * 70)
print("FETCH SUPERADMIN PASSWORD FROM SUPABASE")
print("=" * 70)
print(f"\nSupabase URL: {SUPABASE_URL}")
print(f"Service Key: {SERVICE_KEY[:10]}...{SERVICE_KEY[-5:] if SERVICE_KEY else 'MISSING'}\n")

def get_superadmin_password():
    """Fetch superadmin password from Supabase"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        params = {
            "names": "eq.superadmin",
            "select": "names,passwords,role,created_at"
        }
        
        print("🔍 Fetching superadmin from Supabase...")
        r = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"Status Code: {r.status_code}\n")
        
        if r.status_code == 200:
            data = r.json()
            
            if data and len(data) > 0:
                admin = data[0]
                print("✅ SUPERADMIN FOUND IN CLOUD!\n")
                print("=" * 70)
                print(f"Username: {admin.get('names')}")
                print(f"Password: {admin.get('passwords')}")
                print(f"Role:     {admin.get('role', 'N/A')}")
                print(f"Created:  {admin.get('created_at', 'N/A')}")
                print("=" * 70)
                
                print("\n📋 Use these credentials to login:")
                print(f"   Username: {admin.get('names')}")
                print(f"   Password: {admin.get('passwords')}")
                
                return admin.get('passwords')
            else:
                print("❌ NO SUPERADMIN FOUND IN CLOUD!")
                print("\nThe 'authorized_persons' table has no entry for 'superadmin'.")
                print("You need to create one first.")
                
                create = input("\nWould you like to create a superadmin now? (yes/no): ").strip().lower()
                if create in ['yes', 'y']:
                    new_password = input("Enter password for new superadmin: ").strip()
                    if new_password:
                        create_superadmin(new_password)
                
                return None
        else:
            print(f"❌ ERROR: {r.status_code}")
            print(f"Response: {r.text}")
            
            if r.status_code == 404:
                print("\n⚠️  The 'authorized_persons' table might not exist.")
                print("Run the bootstrap script to create it:")
                print("   python3 credentials/bootstrap_installations_table.py")
            
            return None
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("\n⚠️  Cannot connect to Supabase. Check your internet connection.")
        return None
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return None

def create_superadmin(password):
    """Create a new superadmin in Supabase"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        payload = {
            "names": "superadmin",
            "passwords": password,
            "role": "superadmin"
        }
        
        print("\n📝 Creating superadmin in Supabase...")
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if r.status_code in (200, 201):
            print("✅ SUCCESS! Superadmin created.")
            print(f"\nYour credentials:")
            print(f"   Username: superadmin")
            print(f"   Password: {password}")
            return True
        else:
            print(f"❌ ERROR: {r.status_code}")
            print(f"Response: {r.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    password = get_superadmin_password()
    
    if password:
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print(f"\nYou can now login to the app with:")
        print(f"   Username: superadmin")
        print(f"   Password: {password}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED TO RETRIEVE PASSWORD")
        print("=" * 70)
        print("\nPlease check the errors above and try again.")
