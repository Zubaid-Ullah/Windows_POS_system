# Credentials & Setup Guide

## 1. Supabase Setup
To ensure the Online Check and Cloud features work, you must create the necessary tables in your Supabase project.

1.  Go to your Supabase Dashboard -> **SQL Editor**.
2.  Open the file `supabase_setup.sql` located in this project folder.
3.  Copy the content and paste it into the Supabase SQL Editor.
4.  Click **Run**.

## 2. Super Admin Credentials
Based on the SQL setup, the default Super Admin credentials configured are:

*   **Username**: `superadmin`
*   **Password**: `secure_Sys_2026!`

> **Security Note**: This account is stored in the `authorized_persons` table in the cloud. You can change the password directly in the Supabase Table Editor.

## 3. Secret Keys & Environment
The validation logic relies on Supabase API keys. Ensure you have your `.env` file in the `credentials/` folder or root folder with:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
# Optional but recommended for admin tasks:
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## 4. Feature Logic Confirmation

### Contract Valid + Offline
*   **Behavior**: If the local contract date is valid (e.g., set to 2026), and the intent is disconnected, the system **WILL** allow the user to continue offline seamlessly.
*   **Reason**: The system checks the local database first. If `now < contract_expiry`, it grants access immediately without pinging the server.

### Contract Expired
*   **Behavior**: If the contract is expired, the system **BLOCKS** access.
*   **Recovery**: It automatically attempts to reach the cloud.
    *   If Online & Renewed in Cloud: It updates the local license and lets the user in.
    *   If Offline or Not Renewed: It shows a "Contract Expired" blocking message.

### Super Admin Login
*   **Behavior**: Logging in as `superadmin` **REQUIRES** an active internet connection.
*   **Reason**: High-security account verification involves checking the `authorized_persons` table in real-time.
