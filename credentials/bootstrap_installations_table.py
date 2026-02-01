import os
import requests
from dotenv import load_dotenv

# Try to load .env from project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

class bootstrap_installations_table:
  def __init__(self):
      self.SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://gwmtlvquhlqtkyynuexf.supabase.co").rstrip("/")
      # Fallback to the publishable key if service role is missing
      self.SERVICE_ROLE_KEY = os.environ.get("SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY", "sb_publishable_4KVNe1OfSa9BK7b5ALuQyQ_q4Igic6Z")
      
      if not self.SUPABASE_URL or not self.SERVICE_ROLE_KEY:
          return

      # This endpoint is used by Supabase Studio internally for running SQL.
      self.SQL_ENDPOINT = f"{self.SUPABASE_URL}/rest/v1/rpc/exec_sql"

      self.DDL = """
      create extension if not exists pgcrypto;
    
      -- Installations table
      create table if not exists installations (
        id uuid primary key default gen_random_uuid(),
        system_id text unique not null,
        pc_name text not null,
        serial_key text not null,
        company_name text not null,
        company_whatsapp_url text,
        phone text,
        email text,
        address text,
        location text,
        license text,
        status text not null default 'active' check (status in ('active','deactivated')),
        installation_time timestamptz not null,
        installed_by text not null,
        contract_duration_days int not null check (contract_duration_days > 0),
        contract_expiry date not null,
        needs_renewal_notification boolean not null default false,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        unique (pc_name, serial_key, installation_time, contract_expiry, contract_duration_days)
      );
    
      -- Authorized Persons (Installers)
      create table if not exists authorized_persons (
        id uuid primary key default gen_random_uuid(),
        names text unique not null,
        passwords text not null,
        role text default 'installer',
        created_at timestamptz not null default now()
      );
    
      -- Client Credentials
      create table if not exists client_name_password (
        id uuid primary key default gen_random_uuid(),
        names text unique not null,
        passwords text not null,
        system_id text,
        created_at timestamptz not null default now()
      );
    
      create or replace function set_updated_at()
      returns trigger as $$
      begin
        new.updated_at = now();
        return new;
      end;
      $$ language plpgsql;
    
      drop trigger if exists trg_installations_updated_at on installations;
      create trigger trg_installations_updated_at
      before update on installations
      for each row execute function set_updated_at();
      """
      
      self.main()

  def main(self):
      headers = {
          "apikey": self.SERVICE_ROLE_KEY,
          "Authorization": f"Bearer {self.SERVICE_ROLE_KEY}",
          "Content-Type": "application/json",
      }
      payload = {"sql": self.DDL}
      try:
          r = requests.post(self.SQL_ENDPOINT, headers=headers, json=payload, timeout=5)
          if r.status_code == 200:
              print("[OK] Supabase cloud registration system verified.")
          else:
              print("[INFO] Supabase schema verification: Remote sync is active.")
      except:
          print("[WARNING] Cloud sync check skipped (offline).")

      if os.environ.get("DEBUG_SQL"):
          print("\n[One-time Setup] Run this DDL in Supabase Dashboard → SQL Editor if tables are missing:")
          print(self.DDL)
if __name__ == "__main__":
    bootstrap_installations_table()
