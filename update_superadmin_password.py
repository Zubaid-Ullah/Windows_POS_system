#!/usr/bin/env python3
"""
Quick Superadmin Password Updater
Run this script to update the superadmin password in Supabase cloud
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load credentials
env_path = os.path.join(os.path.dirname(__file__), "credentials", ".env")
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

print("=" * 70)
print("SUPERADMIN PASSWORD UPDATER")
print("=" * 70)

def update_superadmin_password(new_password):
    """Update or create superadmin in authorized_persons table"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation"
        }
        
        # First, check if superadmin exists
        check_url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        check_params = {"names": "eq.superadmin", "select": "id,names,passwords"}
        
        print("\n🔍 Checking if superadmin exists...")
        r = requests.get(check_url, params=check_params, headers=headers, timeout=10)
        
        if r.status_code == 200:
            existing = r.json()
            if existing:
                print(f"   ✅ Found existing superadmin")
                print(f"   Current password: {existing[0].get('passwords', 'N/A')}")
                
                # Update existing
                update_url = f"{SUPABASE_URL}/rest/v1/authorized_persons?names=eq.superadmin"
                update_payload = {"passwords": new_password}
                
                print(f"\n📝 Updating password to: {new_password}")
                r = requests.patch(update_url, json=update_payload, headers=headers, timeout=10)
                
                if r.status_code in (200, 204):
                    print("   ✅ SUCCESS - Password updated!")
                    return True
                else:
                    print(f"   ❌ ERROR: {r.status_code}")
                    print(f"   Response: {r.text}")
                    return False
            else:
                print("   ⚠️  No superadmin found, creating new one...")
                
                # Create new
                create_payload = {
                    "names": "superadmin",
                    "passwords": new_password,
                    "role": "superadmin"
                }
                
                r = requests.post(check_url, json=create_payload, headers=headers, timeout=10)
                
                if r.status_code in (200, 201):
                    print("   ✅ SUCCESS - Superadmin created!")
                    return True
                else:
                    print(f"   ❌ ERROR: {r.status_code}")
                    print(f"   Response: {r.text}")
                    return False
        else:
            print(f"   ❌ ERROR checking table: {r.status_code}")
            print(f"   Response: {r.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def verify_password(password):
    """Test if the password works"""
    try:
        headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/authorized_persons"
        params = {
            "names": "eq.superadmin",
            "passwords": f"eq.{password}",
            "select": "id"
        }
        
        print(f"\n🔐 Testing authentication with new password...")
        r = requests.get(url, params=params, headers=headers, timeout=10)
        
        if r.status_code == 200 and len(r.json() or []) > 0:
            print("   ✅ AUTHENTICATION TEST PASSED!")
            print("   You can now login to the app with this password.")
            return True
        else:
            print("   ❌ AUTHENTICATION TEST FAILED!")
            print("   Something went wrong. Please check manually.")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

# Main execution
if __name__ == "__main__":
    print(f"\nSupabase URL: {SUPABASE_URL}")
    print(f"Service Key: {SERVICE_KEY[:10]}...{SERVICE_KEY[-5:] if SERVICE_KEY else 'MISSING'}")
    
    if not SUPABASE_URL or not SERVICE_KEY:
        print("\n❌ ERROR: Missing Supabase credentials!")
        print("   Check your credentials/.env file")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Get new password from user
    new_password = input("\nEnter the NEW superadmin password you want to set: ").strip()
    
    if not new_password:
        print("❌ Password cannot be empty!")
        sys.exit(1)
    
    # Confirm
    confirm = input(f"\n⚠️  Set superadmin password to: '{new_password}'? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled by user")
        sys.exit(0)
    
    # Update password
    if update_superadmin_password(new_password):
        # Verify it works
        verify_password(new_password)
        
        print("\n" + "=" * 70)
        print("✅ DONE!")
        print("=" * 70)
        print(f"\nYour superadmin credentials are now:")
        print(f"   Username: superadmin")
        print(f"   Password: {new_password}")
        print(f"\nYou can now login to the app using these credentials.")
        print("=" * 70)
    else:
        print("\n❌ Failed to update password. See errors above.")
        sys.exit(1)
