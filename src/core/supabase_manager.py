import os
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv


def load_env_upwards(start_file: str, env_filename: str = ".env") -> Optional[str]:
    """
    Bulletproof .env loader:
    - Starts from this module's file location
    - Walks up parent directories until it finds .env
    - Loads it once found
    Returns the .env path if found, else None.
    """
    start_path = Path(start_file).resolve()
    for parent in [start_path.parent] + list(start_path.parents):
        candidate = parent / env_filename
        if candidate.exists() and candidate.is_file():
            load_dotenv(dotenv_path=str(candidate), override=False)
            return str(candidate)
    return None


class SupabaseManager:
    USERS_TABLE = "authorized_persons"
    CLIENT_TABLE = "CLIENT_NAME_PASSWORD"
    INSTALL_TABLE = "installations"

    def __init__(self):
        import sys
        
        # 1. Determine Base Path for Credentials
        if getattr(sys, 'frozen', False):
            # EXE: Look in credentials folder NEXT TO the exe first (Priority: Updates)
            base_dir = os.path.dirname(sys.executable)
            env_path = os.path.join(base_dir, "credentials", ".env")
            
            loaded = False
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
                self._log_init(f"Loaded EXTERNAL .env from: {env_path}")
                loaded = True
            else:
                 self._log_init(f"⚠️ External .env NOT FOUND at: {env_path}")

            # Fallback: Try internal bundle (Embedded keys)
            if not loaded and hasattr(sys, '_MEIPASS'):
                 internal_env = os.path.join(sys._MEIPASS, "credentials", ".env")
                 if os.path.exists(internal_env):
                     load_dotenv(internal_env, override=True)
                     self._log_init(f"Loaded INTERNAL (Bundled) .env from: {internal_env}")
                 else:
                     self._log_init(f"❌ Internal .env NOT FOUND at: {internal_env}")

        else:
            # DEV: Look upwards from this file
            env_path = load_env_upwards(__file__)
            if not env_path:
                 # Fallback manual check
                 root = Path(__file__).resolve().parent.parent.parent
                 env_path = str(root / "credentials" / ".env")
            
            if env_path and os.path.exists(env_path): 
                load_dotenv(env_path, override=True)
                self._log_init(f"Loaded .env from: {env_path}")

        self.url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        self._fix_ssl()
        
        # DEBUG: Log key status (safe, partial)
        k_status = f"{self.key[:5]}...{self.key[-5:]}" if self.key and len(self.key) > 10 else "None/Short"
        # Mask URL for security
        self._log(f"Supabase Init: URL=[HIDDEN], Key={k_status}")

    def _sanitize(self, msg: Any) -> str:
        """Hide sensitive URLs in log/output messages"""
        s_msg = str(msg)
        if self.url:
            s_msg = s_msg.replace(self.url, "[HIDDEN-URL]")
        # Also catch the known hardcoded URL just in case self.url is not set yet
        s_msg = s_msg.replace("gwmtlvquhlqtkyynuexf.supabase.co", "[HIDDEN-URL]")
        return s_msg

    def _log_init(self, msg):
        # Quick helper to log before full init
        self._log(msg)

    def _log(self, msg):
        try:
            # Log to file next to executable/script
            import sys
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
            else:
                base = os.path.dirname(os.path.abspath(__file__))
            
            sanitized_msg = self._sanitize(msg)
            with open(os.path.join(base, "debug_connectivity.txt"), "a", encoding='utf-8') as f:
                f.write(f"[{datetime.now().time()}] {sanitized_msg}\n")
        except: pass

    def _headers(self) -> Dict[str, str]:
        return {"apikey": self.key, "Authorization": f"Bearer {self.key}"}

    def _url(self, table_name: str) -> str:
        return f"{self.url}/rest/v1/{table_name}"

    def _fix_ssl(self):
        import sys
        if getattr(sys, 'frozen', False):
            self._log("Running in FROZEN (EXE) mode")
            # Potential locations for certifi in PyInstaller _MEIPASS
            # 1. Root of _MEIPASS (if collected as binary)
            # 2. Inside certifi folder (collect-all)
            base_temp = getattr(sys, '_MEIPASS', '')
            candidates = [
               os.path.join(base_temp, 'certifi', 'cacert.pem'),
               os.path.join(base_temp, 'cacert.pem'),
               os.path.join(base_temp, 'cert.pem')
            ]
            
            found = False
            for c in candidates:
                if os.path.exists(c):
                    self._log(f"Found cert at: {c}")
                    os.environ['REQUESTS_CA_BUNDLE'] = c
                    found = True
                    break
            
            if not found:
                 self._log(f"⚠️ No SSL cert found in _MEIPASS. searched: {candidates}")
        else:
             self._log("Running in DEV (Script) mode")

    def check_connection(self) -> bool:
        """
        Robust check with socket ping fallback, logging, and SSL Fallback.
        """
        self._log("Checking connection...")
        try:
            # 1) PRE-CHECK: Fast socket ping (bypass OS-level DNS logic issues if any)
            import socket
            test_hosts = [("8.8.8.8", 53), ("1.1.1.1", 53)]
            socket_success = False
            for host, port in test_hosts:
                try:
                    self._log(f"Socket pinging {host}:{port}...")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    if sock.connect_ex((host, port)) == 0:
                        self._log(f"  -> Socket success for {host}")
                        socket_success = True
                        sock.close()
                        break
                    sock.close()
                except: pass
            
            if not socket_success:
                self._log("⚠️ Socket ping failed. No basic IP connectivity.")

            # 2) HTTP Pings
            endpoints = ["https://www.google.com/generate_204", "https://www.cloudflare.com"]
            for endpoint in endpoints:
                try:
                    self._log(f"Pinging {endpoint}...")
                    requests.get(endpoint, timeout=3)
                    self._log("  -> HTTP Success")
                    return True
                except requests.exceptions.SSLError as e:
                    self._log(f"  -> SSL Error: {e}")
                    self._log("  -> Retrying with verify=False (Insecure Fallback)")
                    try:
                        requests.get(endpoint, timeout=3, verify=False)
                        self._log("  -> Success (Insecure)")
                        return True
                    except Exception as e2:
                        self._log(f"  -> Insecure Retry Failed: {e2}")
                        
                except Exception as e:
                    self._log(f"  -> HTTP Failed: {e}")

            # 3) Supabase check
            try:
                if not self.url:
                    self._log("⚠️ Supabase URL is empty, skipping ping.")
                else:
                    self._log("Pinging Supabase (Cloud URL)...")
                    r = requests.get(f"{self.url}/rest/v1/", headers={"apikey": self.key}, timeout=5)
                    if r.status_code in (200, 401):
                        self._log("  -> Supabase Success")
                        return True
            except Exception as e:
                self._log(f"  -> Supabase Failed: {e}")
                # Try fallback
                try: 
                    requests.get(f"{self.url}/rest/v1/", headers={"apikey": self.key}, timeout=5, verify=False)
                    self._log("  -> Supabase Success (Insecure)")
                    return True
                except: pass

            self._log("❌ All connection checks failed.")
            return False

        except Exception as e:
            self._log(f"❌ Critical check error: {e}")
            return False

    # -----------------------------
    # Installer (authorized person) methods
    # -----------------------------

    def get_installers(self) -> List[str]:
        """Fetch installer names strictly from cloud"""
        self._log("Fetching installers...")
        try:
            # Try standard spelling 'authorized_persons'
            params = {"select": "names", "order": "names.asc"}
            url = self._url(self.USERS_TABLE)
            self._log(f"GET [HIDDEN]/{self.USERS_TABLE}")
            
            r = requests.get(url, params=params, headers=self._headers(), timeout=10)
            self._log(f"  -> Status: {r.status_code}")
            
            # Fallback for 404 (Table not found) - try British spelling
            if r.status_code == 404:
                self._log("  -> 404 Not Found. Trying British spelling 'authorised_persons'...")
                alt_url = self._url("authorised_persons")
                r = requests.get(alt_url, params=params, headers=self._headers(), timeout=10)
                self._log(f"  -> Alt Status: {r.status_code}")

            if r.status_code == 200:
                data = r.json() or []
                self._log(f"  -> Data count: {len(data)}")
                if not data:
                    self._log("⚠️ WARNING: Table exists but returned no rows. Possible RLS (Row Level Security) blocking reads? Ensure Policy allows SELECT.")
                
                # Robust extraction (handle 'name' or 'names')
                results = []
                for row in data:
                    name = row.get("names") or row.get("name") or row.get("username")
                    if name: results.append(name)
                return results
                
            self._log(f"❌ Failed to fetch installers. Reponse: {r.text}")
            return []
        except Exception as e:
            self._log(f"❌ get_installers Error: {e}")
            return []

    def verify_installer(self, username, password) -> bool:
        """Online verification for installers / SuperAdmin"""
        try:
            username_cleaned = username.strip().lower()
            password_cleaned = password.strip()

            # 1. SuperAdmin Special Handling
            if username_cleaned == "superadmin":
                self._log("🛡️ SuperAdmin Login Attempt detected...")
                
                # A. Try Secret Key from 'keystable' first
                if self.verify_secret_key(password_cleaned):
                    self._log("✅ SuperAdmin authenticated via Secret Key.")
                    return True
                
                # B. Try Fallback: Check if any user in 'authorized_persons' has role='superadmin' and matching password
                self._log("🔄 Secret Key failed. Trying fallback to Cloud SuperAdmin password...")
                params = {"role": "eq.superadmin", "passwords": f"eq.{password_cleaned}", "select": "id"}
                r = requests.get(self._url(self.USERS_TABLE), params=params, headers=self._headers(), timeout=10)
                
                if r.status_code == 200 and len(r.json() or []) > 0:
                    self._log("✅ SuperAdmin authenticated via Cloud Role/Password.")
                    return True
                
                self._log("❌ SuperAdmin authentication failed (Both Secret Key and Cloud Role check).")
                return False
            
            else:
                # 2. Regular installer verification by username and password
                params = {"names": f"eq.{username.strip()}", "passwords": f"eq.{password_cleaned}", "select": "id"}
                r = requests.get(self._url(self.USERS_TABLE), params=params, headers=self._headers(), timeout=10)
                
                if r.status_code == 200 and len(r.json() or []) > 0:
                    return True
                
                self._log(f"❌ Regular installer verification failed for user: {username}")
                return False
        except Exception as e:
            self._log(f"❌ verify_installer Exception: {e}")
            return False

    def verify_secret_key(self, key: str) -> bool:
        """
        Verifies a secret key against the 'keystable' in Supabase.
        Used for superadmin-level activations and contract updates.
        """
        try:
            key_val = key.strip()
            params = {"secret_key": f"eq.{key_val}", "select": "id"}
            url = self._url("keystable")
            self._log(f"🔍 Checking keystable for key [HIDDEN] at {url}")
            
            r = requests.get(url, params=params, headers=self._headers(), timeout=10)
            
            if r.status_code == 200:
                data = r.json() or []
                match = len(data) > 0
                self._log(f"✅ Keystable response received. Match found: {match}")
                return match
            else:
                self._log(f"❌ Keystable query failed. Status: {r.status_code} - {r.text}")
                # Try fallback column name 'secret key' just in case
                self._log("🔄 Trying fallback column name 'secret key'...")
                params_fb = {"secret key": f"eq.{key_val}", "select": "id"}
                r_fb = requests.get(url, params=params_fb, headers=self._headers(), timeout=10)
                if r_fb.status_code == 200 and len(r_fb.json() or []) > 0:
                     self._log("✅ Match found using fallback column name 'secret key'.")
                     return True
                return False
        except Exception as e:
            self._log(f"❌ verify_secret_key error: {e}")
            return False


    # -----------------------------
    # Client credential methods
    # -----------------------------

    def register_client(self, username, password, system_id=None) -> bool:
        """Save new client credentials to cloud"""
        try:
            # Include created_at since it has a NOT NULL constraint without a default in DB
            payload = {
                "names": username.strip(), 
                "passwords": password.strip(),
                "created_at": datetime.now().isoformat()
            }
            r = requests.post(self._url(self.CLIENT_TABLE), json=payload, headers={**self._headers(), "Content-Type": "application/json"}, timeout=10)
            
            if r.status_code in (200, 201):
                return True
            print(self._sanitize(f"❌ register_client failed: {r.status_code} - {r.text}"))
            return False
        except Exception as e:
            print(self._sanitize(f"❌ register_client error: {e}"))
            return False

    def verify_client(self, username, password) -> bool:
        """Online verification for client accounts"""
        try:
            params = {"names": f"eq.{username.strip()}", "passwords": f"eq.{password.strip()}", "select": "id"}
            r = requests.get(self._url(self.CLIENT_TABLE), params=params, headers=self._headers(), timeout=10)
            return r.status_code == 200 and len(r.json() or []) > 0
        except:
            return False

    def get_clients(self) -> List[str]:
        """Fetch all client names from cloud"""
        try:
            params = {"select": "names", "order": "names.asc"}
            r = requests.get(self._url(self.CLIENT_TABLE), params=params, headers=self._headers(), timeout=10)
            if r.status_code == 200:
                data = r.json() or []
                return [row.get("names") for row in data if row.get("names")]
            return []
        except:
            return []

    # -----------------------------
    # Installation methods
    # -----------------------------

    def update_company_details(self, system_id: str, payload: Dict[str, Any]) -> bool:
        """
        PATCH installations by system_id.
        """
        try:
            system_id = (system_id or "").strip()
            if not system_id or not isinstance(payload, dict):
                return False

            headers = {**self._headers(), "Content-Type": "application/json", "Prefer": "return=minimal"}
            url = f"{self._url(self.INSTALL_TABLE)}?system_id=eq.{system_id}"

            r = requests.patch(url, json=payload, headers=headers, timeout=10)
            return r.status_code in (200, 204)

        except Exception as e:
            print(self._sanitize(f"❌ update_company_details error: {e}"))
            return False

    def upsert_installation(self, payload: Dict[str, Any]) -> bool:
        """
        Upsert into installations (requires a UNIQUE constraint e.g., system_id UNIQUE).
        """
        try:
            if not isinstance(payload, dict) or not payload:
                return False

            headers = {
                **self._headers(),
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            }

            # Add on_conflict parameter to enable true UPSERT (update if exists)
            url = f"{self._url(self.INSTALL_TABLE)}?on_conflict=system_id"
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            if r.status_code in (200, 201, 204, 409):
                return True

            print(self._sanitize(f"❌ upsert_installation failed: {r.status_code} - {r.text}"))
            return False

        except Exception as e:
            print(self._sanitize(f"❌ upsert_installation error: {e}"))
            return False

    def get_installation_status(self, system_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns status + contact info for a given system_id.
        """
        try:
            system_id = (system_id or "").strip()
            if not system_id:
                return None

            # Added pharmacy_active and store_active for modular activation control
            params = {
                "select": "status,company_name,phone,email,address,location,license,contract_expiry,system_id,pc_name,serial_key,installation_time,installed_by,contract_duration_days,pharmacy_active,store_active",
                "system_id": f"eq.{system_id}",
                "limit": "1",
            }

            r = requests.get(self._url(self.INSTALL_TABLE), params=params, headers=self._headers(), timeout=10)
            if r.status_code != 200:
                print(self._sanitize(f"❌ get_installation_status failed: {r.status_code} - {r.text}"))
                return None

            data = r.json() or []
            return data[0] if data else None

        except Exception as e:
            print(self._sanitize(f"❌ get_installation_status error: {e}"))
            return None

    def log_activation_attempt(self, installer_name: str, system_id: str, pc_name: str) -> bool:
        """
        Securely logs an activation attempt by an installer to the cloud.
        Useful for superadmin to monitor unauthorized or repeated activation attempts.
        """
        try:
            payload = {
                "installer_name": installer_name,
                "system_id": system_id,
                "pc_name": pc_name,
                "attempt_time": datetime.now().isoformat(),
                "details": "Local activation attempt detected."
            }
            # Note: Superadmin should create a table named 'activation_logs' in Supabase
            r = requests.post(self._url("activation_logs"), json=payload, headers=self._headers(), timeout=10)
            return r.status_code in (200, 201, 204)
        except Exception as e:
            print(self._sanitize(f"❌ log_activation_attempt error: {e}"))
            return False


# Singleton instance
supabase_manager = SupabaseManager()
