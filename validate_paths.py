# Path Validation Test
import os
import sys

def test_paths():
    print(f"Platform: {sys.platform}")
    print(f"OS Name: {os.name}")
    print(f"Path Separator: {os.sep}")
    
    test_cases = [
        ("credentials", "company_qr.png"),
        ("credentials", "useraccount.txt"),
        ("data", "bills"),
        ("data", "kyc", "test.jpg")
    ]
    
    print("\nVerifying Path Joining:")
    for parts in test_cases:
        path = os.path.join(*parts)
        print(f"Joined {parts} -> {path}")
        
        # On Windows, os.sep is \. On Mac/Linux, it's /.
        # Even if we are on Mac, we can simulate what happens if we were on Windows
        # by checking if we used os.path.join instead of hardcoded slashes.
        if "/" in path and os.name == 'nt':
             print("  FAILED: Found forward slash on Windows")
        elif "\\" in path and os.name != 'nt':
             # Note: Python on Windows can accept / sometimes, but Windows style is \
             pass

if __name__ == "__main__":
    test_paths()
