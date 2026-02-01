import os
from supabase import create_client

SUPABASE_URL = os.environ["https://gwmtlvquhlqtkyynuexf.supabase.co"]
# server/admin only
SUPABASE_KEY = os.environ["sb_publishable_4KVNe1OfSa9BK7b5ALuQyQ_q4Igic6Z"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_installations():
    res = supabase.table("installations").select(
        "id, system_id, pc_name, company_name, status, contract_expiry, needs_renewal_notification, installed_by, installation_time"
    ).order("installation_time", desc=True).execute()

    rows = res.data or []
    for r in rows:
        print(f"- {r['system_id']} | {r['pc_name']} | {r['company_name']} | {r['status']} | expiry={r['contract_expiry']} | id={r['id']}")

def set_status(system_id: str, status: str):
    if status not in ("active", "deactivated"):
        raise ValueError("status must be 'active' or 'deactivated'")

    res = supabase.table("installations").update({"status": status}).eq("system_id", system_id).execute()
    if not res.data:
        print("❌ system_id not found:", system_id)
        return
    print("✅ Updated:", system_id, "->", status)

if __name__ == "__main__":
    print("All installations:")
    list_installations()

    # Example: deactivate a system
    # set_status("SYS-ABCDEF123456", "deactivated")
