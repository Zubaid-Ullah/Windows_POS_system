#!/usr/bin/env python3
"""
GUI Hang Fixes - Verification Script
This script helps verify that all GUI hang fixes are working correctly.
"""

import os
import sys

def check_file_for_patterns(filepath, bad_patterns, good_patterns):
    """Check if file has been properly fixed."""
    if not os.path.exists(filepath):
        return {"status": "missing", "file": filepath}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    successes = []
    
    # Check for bad patterns (should NOT exist)
    for pattern in bad_patterns:
        if pattern in content:
            issues.append(f"❌ Found bad pattern: {pattern}")
    
    # Check for good patterns (should exist)
    for pattern in good_patterns:
        if pattern in content:
            successes.append(f"✅ Found good pattern: {pattern}")
        else:
            issues.append(f"⚠️  Missing good pattern: {pattern}")
    
    return {
        "status": "pass" if not issues else "fail",
        "file": filepath,
        "issues": issues,
        "successes": successes
    }

def main():
    print("=" * 80)
    print("GUI HANG FIXES - VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    base_path = "/Users/apple/Documents/GitHub/POS platforms/Windows_POS_system"
    
    checks = [
        {
            "name": "create_account_stepper.py",
            "file": f"{base_path}/src/ui/views/onboarding/create_account_stepper.py",
            "bad_patterns": [
                "class UserFetcher(QThread)",
                "users = supabase_manager.get_installers()",  # Direct call in _do_refresh
            ],
            "good_patterns": [
                "from src.core.blocking_task_manager import task_manager",
                "task_manager.run_task(fetch_installers",
            ]
        },
        {
            "name": "settings_view.py",
            "file": f"{base_path}/src/ui/views/settings_view.py",
            "bad_patterns": [
                "class SettingsSyncWorker(QThread)",
                "self.sync_thread = SettingsSyncWorker",
                "def cleanup_thread(self)",
            ],
            "good_patterns": [
                "from src.core.blocking_task_manager import task_manager",
                "task_manager.run_task(sync_to_cloud",
                "task_manager.run_task(load_from_cloud",
            ]
        },
        {
            "name": "super_admin_view.py",
            "file": f"{base_path}/src/ui/views/super_admin_view.py",
            "bad_patterns": [
                "class CloudWorker(QThread)",
                "self.worker = CloudWorker()",
            ],
            "good_patterns": [
                "from src.core.blocking_task_manager import task_manager",
                "task_manager.run_task(fetch_cloud_data",
            ]
        },
        {
            "name": "credentials_view.py",
            "file": f"{base_path}/src/ui/views/credentials_view.py",
            "bad_patterns": [
                "class FetchWorker(QThread)",
                "class AbortWorker(QThread)",
                "class ShutdownScheduler(QThread)",
                "class ExtendWorker(QThread)",
                "class StatusToggleWorker(QThread)",
            ],
            "good_patterns": [
                "from src.core.blocking_task_manager import task_manager",
                "task_manager.run_task(fetch_installations",
                "task_manager.run_task(abort_shutdown",
                "task_manager.run_task(schedule_shutdown",
                "task_manager.run_task(extend_contract",
                "task_manager.run_task(toggle_status",
            ]
        },
        {
            "name": "login_window.py",
            "file": f"{base_path}/src/ui/views/onboarding/login_window.py",
            "bad_patterns": [
                "class UserFetcher(QThread)",
                "class AuthWorker(QThread)",
                "from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread",
            ],
            "good_patterns": [
                "from src.core.blocking_task_manager import task_manager",
                "task_manager.run_task(fetch_users",
                "task_manager.run_task(authenticate",
            ]
        },
    ]
    
    total_checks = len(checks)
    passed = 0
    failed = 0
    
    for check in checks:
        print(f"\n{'=' * 80}")
        print(f"Checking: {check['name']}")
        print(f"{'=' * 80}")
        
        result = check_file_for_patterns(
            check['file'],
            check['bad_patterns'],
            check['good_patterns']
        )
        
        if result['status'] == 'missing':
            print(f"❌ FILE NOT FOUND: {result['file']}")
            failed += 1
            continue
        
        if result['successes']:
            print("\n✅ SUCCESSES:")
            for success in result['successes']:
                print(f"  {success}")
        
        if result['issues']:
            print("\n❌ ISSUES:")
            for issue in result['issues']:
                print(f"  {issue}")
            failed += 1
        else:
            print("\n🎉 ALL CHECKS PASSED!")
            passed += 1
    
    print(f"\n{'=' * 80}")
    print("FINAL SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Files Checked: {total_checks}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL GUI HANG FIXES VERIFIED SUCCESSFULLY! 🎉")
        print("\nNext Steps:")
        print("1. Test the application with slow/no network")
        print("2. Verify all user workflows work correctly")
        print("3. Check for any GUI freezes during operations")
        print("4. Monitor for memory leaks or thread accumulation")
        return 0
    else:
        print("\n⚠️  SOME FIXES NEED ATTENTION")
        print("\nPlease review the issues above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
