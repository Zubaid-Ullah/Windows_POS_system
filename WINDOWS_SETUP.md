# Windows Setup Guide

## Prerequisites
- Python 3.11 or higher
- Git for Windows
- Internet connection

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Zubaid-Ullah/POS_system.git
cd POS_system
```

### 2. Configure Credentials
```bash
# Copy the template
copy credentials\.env.example credentials\.env

# Edit credentials\.env with your Supabase credentials
notepad credentials\.env
```

**Important:** Add your actual Supabase URL and Service Role Key to the `.env` file.

### 3. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python main.py
```

## Troubleshooting

### App Hangs After Internet Check
**Symptoms:** App shows "Checking internet connection..." then freezes or closes.

**Solutions:**
1. **Check credentials file exists:**
   ```bash
   dir credentials\.env
   ```
   If missing, copy from template (see step 2 above)

2. **Verify credentials are valid:**
   - Open `credentials\.env` in notepad
   - Ensure `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are filled in
   - No quotes or extra spaces

3. **Check directory structure:**
   ```bash
   dir data\backups
   dir data\bills
   dir data\kyc
   ```
   All should exist. If missing, create them:
   ```bash
   mkdir data\backups
   mkdir data\bills
   mkdir data\kyc
   ```

4. **Remove old database files:**
   ```bash
   del *.db
   del data\*.db
   ```
   Let the app create fresh databases on first run.

### Database Errors
**Symptoms:** "Unable to open database file" or "Database is locked"

**Solutions:**
1. Delete any existing `.db` files:
   ```bash
   del afex_store.db
   del afex_pharmacy.db
   del data\pos_system.db
   ```

2. Ensure you have write permissions in the directory

3. Run the app again - it will create fresh databases

### Import Errors
**Symptoms:** "ModuleNotFoundError" when running the app

**Solutions:**
1. Ensure virtual environment is activated:
   ```bash
   .venv\Scripts\activate
   ```
   You should see `(.venv)` in your command prompt

2. Reinstall dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Permission Errors
**Symptoms:** "Access denied" or "Permission denied"

**Solutions:**
1. Run Command Prompt as Administrator
2. Check antivirus isn't blocking Python
3. Ensure the project folder isn't in a protected location (like C:\Program Files)

## First Run

On first run, the app will:
1. Check internet connectivity
2. Create local database files (`afex_store.db`, `afex_pharmacy.db`)
3. Show the registration/onboarding window
4. Guide you through account setup

## Getting Supabase Credentials

If you don't have Supabase credentials:

1. Go to https://supabase.com
2. Create a free account
3. Create a new project
4. Go to Project Settings → API
5. Copy:
   - **Project URL** → Use as `SUPABASE_URL`
   - **service_role key** → Use as `SUPABASE_SERVICE_ROLE_KEY`

## Support

For additional help, check:
- Main README: [README.md](README.md)
- Project Documentation: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)
- Superadmin Guide: [SUPERADMIN_FIX_FINAL.md](SUPERADMIN_FIX_FINAL.md)
