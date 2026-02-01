import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.core.supabase_manager import supabase_manager
from credentials.bootstrap_installations_table import bootstrap_installations_table
import threading
import time

def test_connectivity_logic():
    print("Testing optimized check_connection...")
    start = time.time()
    online = supabase_manager.check_connection()
    end = time.time()
    print(f"Connection check result: {online} (took {end-start:.2f}s)")

def test_bootstrap_logic():
    print("Testing non-blocking bootstrap logic...")
    thread = threading.Thread(target=bootstrap_installations_table, daemon=True)
    start = time.time()
    thread.start()
    end = time.time()
    print(f"Bootstrap thread started in {end-start:.4f}s")
    print("Main thread is free to proceed with GUI.")
    
    # Wait a bit to see if bootstrap finishes or logs anything
    time.sleep(2)
    print("Verification script finished.")

if __name__ == "__main__":
    test_connectivity_logic()
    test_bootstrap_logic()
