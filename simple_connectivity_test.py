#!/usr/bin/env python3
"""
Simple Connectivity Test - No external dependencies
"""

import socket
import time
import urllib.request

def test_connectivity():
    print("🌐 POS System Connectivity Test")
    print("=" * 40)

    # Test basic socket connection
    print("Testing socket connections...")

    test_hosts = [
        ("Google DNS", "8.8.8.8", 53),
        ("Cloudflare DNS", "1.1.1.1", 53),
    ]

    for name, host, port in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            start_time = time.time()
            result = sock.connect_ex((host, port))
            elapsed = time.time() - start_time

            if result == 0:
                print(f"✅ {name}: Connected in {elapsed:.2f}s")
            else:
                print(f"❌ {name}: Connection failed")
            sock.close()
        except Exception as e:
            print(f"❌ {name}: Error - {e}")

    print("\nTesting HTTP connections...")

    # Test HTTP connections (basic)
    test_urls = [
        ("Google", "http://www.google.com"),
        ("HTTPBin", "http://httpbin.org/get"),
    ]

    for name, url in test_urls:
        try:
            start_time = time.time()
            # Use urllib instead of requests
            req = urllib.request.Request(url, headers={'User-Agent': 'POS-System-Test/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                elapsed = time.time() - start_time
                if response.status == 200:
                    print(f"✅ {name}: HTTP {response.status} in {elapsed:.2f}s")
                else:
                    print(f"⚠️ {name}: HTTP {response.status}")
        except Exception as e:
            print(f"❌ {name}: Failed - {str(e)[:50]}...")

    print("\n" + "=" * 40)
    print("If socket connections work but HTTP fails:")
    print("  → Firewall/antivirus may be blocking the application")
    print("  → Try running as administrator or disabling firewall temporarily")
    print("\nIf both fail:")
    print("  → Check your actual internet connection")
    print("  → Try different network or contact IT support")
    print("\nThe POS system should now allow offline mode even if checks fail.")

if __name__ == "__main__":
    test_connectivity()