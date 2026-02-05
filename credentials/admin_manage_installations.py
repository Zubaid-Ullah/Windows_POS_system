import os
import json
import platform
import subprocess
import uuid
import socket
from datetime import datetime, timedelta, timezone, date
from random import random

from dateutil.parser import isoparse
from supabase import create_client

SUPABASE_URL = os.environ["https://gwmtlvquhlqtkyynuexf.supabase.co"]
# server/admin only
SUPABASE_KEY = os.environ["sb_publishable_4KVNe1OfSa9BK7b5ALuQyQ_q4Igic6Z"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Local file where we store stable system_id on that PC
LOCAL_SYSTEM_ID_PATH = os.path.expanduser("~/.afex_pos_system_id.json")

def load_or_create_system_id() -> str:
    if os.path.exists(LOCAL_SYSTEM_ID_PATH):
        with open(LOCAL_SYSTEM_ID_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["system_id"]

    system_id = "SYS-" + uuid.uuid4().hex[:12].upper()
    os.makedirs(os.path.dirname(LOCAL_SYSTEM_ID_PATH), exist_ok=True)
    with open(LOCAL_SYSTEM_ID_PATH, "w", encoding="utf-8") as f:
        json.dump({"system_id": system_id}, f)
    return system_id

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def compute_expiry(installation_time_iso: str, duration_days: int) -> date:
    start = isoparse(installation_time_iso)
    expiry_dt = start + timedelta(days=duration_days)
    return expiry_dt.date()

def build_key_label(pc_name: str, serial_key: str, start_iso: str, expiry_date: date, duration_days: int) -> str:
    # Example: (PC-01)-ABC123-(2026-01-16T14:30:00Z - 2026-07-15)-(180)
    return f"({pc_name})-{serial_key}-({start_iso} - {expiry_date.isoformat()})-({duration_days})"

def upsert_installation(payload: dict) -> dict:
    """
    Upsert by system_id (unique).
    """
    # Try fetch existing
    existing = supabase.table("installations").select("id, system_id, status").eq("system_id", payload["system_id"]).execute()
    if existing.data:
        # Update
        updated = supabase.table("installations").update(payload).eq("system_id", payload["system_id"]).execute()
        row = updated.data[0]
        print("✅ Updated existing installation")
        print("system_id:", row["system_id"], "| status:", row["status"])
        return row

    # Insert
    created = supabase.table("installations").insert(payload).execute()
    row = created.data[0]
    print("🆕 Created new installation")
    print("system_id:", row["system_id"], "| status:", row["status"])
    return row


def get_serial_number():
    current_os = platform.system().lower()
    serial = "Unknown"

    try:
        if "windows" in current_os:
            # Uses WMIC to query the BIOS serial number
            command = "wmic bios get serialnumber"
            output = subprocess.check_output(command, shell=True).decode()
            serial = output.split("\n")[1].strip()

        elif "darwin" in current_os:
            # Uses ioreg to get the hardware serial number on macOS
            command = "ioreg -l | grep IOPlatformSerialNumber"
            output = subprocess.check_output(command, shell=True).decode()
            serial = output.split("=")[-1].replace('"', "").strip()

        elif "linux" in current_os:
            # Tries to read from the DMI sysfs files which are often world-readable
            # Fallback for systems where dmidecode requires sudo
            paths = [
                "/sys/class/dmi/id/product_serial",
                "/sys/class/dmi/id/board_serial"
            ]
            for path in paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        serial = f.read().strip()
                        if serial: break

            # If sysfs fails, try unprivileged udevadm (common on many distros)
            if not serial or serial == "Unknown":
                try:
                    output = subprocess.check_output(
                        "udevadm info --query=property --name=/dev/sda | grep ID_SERIAL_SHORT", shell=True).decode()
                    serial = output.split("=")[-1].strip()
                except:
                    pass

    except Exception as e:
        return f"Error: {str(e)}"

    return serial
def main():
    system_id = load_or_create_system_id()

    # If you want auto pc_name from machine:
    pc_name = socket.gethostname()

    # ---- YOU FILL THESE (from your installer UI / config) ----
    serial_key = f"{get_serial_number()}"
    company_name = "Afexnology"
    company_whatsapp_url = "https://wa.me/937XXXXXXXXX"
    phone = "+93XXXXXXXXX"
    address = "Kabul, Afghanistan, ... full address"
    email = "support@yourdomain.com"
    location = address  # or separate
    license_name = f"Afex-POS-LICENSE-{random.randint(0, 9999):04}"
    installed_by = "developer-or-superadmin-name"
    contract_duration_days = 180
    # ----------------------------------------------------------

    installation_time = utc_now_iso()
    contract_expiry = compute_expiry(installation_time, contract_duration_days)
    needs_renewal_notification = False

    key_label = build_key_label(pc_name, serial_key, installation_time, contract_expiry, contract_duration_days)
    print("KEY LABEL:", key_label)

    payload = {
        "system_id": system_id,
        "pc_name": pc_name,
        "serial_key": serial_key,
        "company_name": company_name,
        "company_whatsapp_url": company_whatsapp_url,
        "phone": phone,
        "address": address,
        "email": email,
        "location": location,
        "license": license_name,
        "installation_time": installation_time,
        "installed_by": installed_by,
        "contract_duration_days": contract_duration_days,
        "contract_expiry": contract_expiry.isoformat(),
        "needs_renewal_notification": needs_renewal_notification,
        # status is set by admin; do NOT set here unless you want
    }

    row = upsert_installation(payload)
    print("RESULT:", {"system_id": row["system_id"], "status": row["status"]})

if __name__ == "__main__":
    main()
