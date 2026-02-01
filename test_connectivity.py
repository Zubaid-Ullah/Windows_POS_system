#!/usr/bin/env python3
"""
Connectivity Test Script
Run this to diagnose internet connectivity issues in your POS system
"""

import requests
import time
import socket

def test_basic_connectivity():
    """Test basic internet connectivity"""
    print("🔍 Testing Basic Internet Connectivity...")
    print("=" * 50)

    test_urls = [
        ("Google", "https://www.google.com"),
        ("Cloudflare", "https://www.cloudflare.com"),
        ("Microsoft", "https://www.microsoft.com"),
        ("Supabase", "https://gwmtlvquhlqtkyynuexf.supabase.co")
    ]

    results = {}

    for name, url in test_urls:
        print(f"Testing {name} ({url})...")
        try:
            start_time = time.time()
            response = requests.head(url, timeout=10)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                print(f"  ✅ SUCCESS - {elapsed:.2f}s")
                results[name] = True
            else:
                print(f"  ❌ FAILED - Status: {response.status_code}")
                results[name] = False

        except requests.exceptions.RequestException as e:
            print(f"  ❌ FAILED - {str(e)}")
            results[name] = False
        except Exception as e:
            print(f"  ❌ ERROR - {str(e)}")
            results[name] = False

        print()

    return results

def test_dns_resolution():
    """Test DNS resolution"""
    print("🔍 Testing DNS Resolution...")
    print("=" * 50)

    test_domains = [
        "google.com",
        "supabase.co",
        "cloudflare.com"
    ]

    for domain in test_domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {domain} -> DNS resolution failed: {e}")

def check_firewall_settings():
    """Check for common firewall issues"""
    print("\n🔍 Firewall & Proxy Check...")
    print("=" * 50)

    # Check if running with elevated privileges (might help with some firewall issues)
    import os
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        print(f"Running as administrator: {'✅ Yes' if is_admin else '❌ No'}")
    except:
        print("Administrator check: Not applicable (not Windows)")

    # Check proxy settings
    proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if proxy:
        print(f"HTTP Proxy detected: {proxy}")
    else:
        print("No HTTP proxy detected")

    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if https_proxy:
        print(f"HTTPS Proxy detected: {https_proxy}")
    else:
        print("No HTTPS proxy detected")

def main():
    print("🌐 POS System Connectivity Diagnostic Tool")
    print("=" * 50)
    print("This tool will help diagnose internet connectivity issues")
    print("that might be preventing your POS system from starting.\n")

    # Test DNS first
    test_dns_resolution()

    # Test connectivity
    results = test_basic_connectivity()

    # Check firewall/proxy
    check_firewall_settings()

    # Summary
    print("\n📊 SUMMARY")
    print("=" * 50)

    internet_ok = any(results.get(url, False) for url in ["Google", "Cloudflare", "Microsoft"])
    supabase_ok = results.get("Supabase", False)

    if internet_ok:
        print("✅ Basic internet connectivity: WORKING")
    else:
        print("❌ Basic internet connectivity: FAILED")
        print("   Check your network connection and firewall settings.")

    if supabase_ok:
        print("✅ Supabase connectivity: WORKING")
    else:
        print("❌ Supabase connectivity: FAILED")
        print("   This may be blocked by firewall/antivirus.")
        print("   The POS system can still work in offline/local mode.")

    print("\n💡 RECOMMENDATIONS:")
    print("   1. If internet works but Supabase fails, the POS will allow 'local mode'")
    print("   2. Check if antivirus/firewall is blocking the application")
    print("   3. Try running the POS system - it should bypass the connectivity check")
    print("   4. If issues persist, temporarily disable antivirus during testing")

if __name__ == "__main__":
    main()