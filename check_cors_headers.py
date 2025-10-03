#!/usr/bin/env python3
"""
Check CORS headers for a given endpoint and origin.
Usage: python check_cors_headers.py <url> <origin>
Example: python check_cors_headers.py https://your-aws-hostname/api/users/login/ https://www.chopsmo.site
"""
import sys
import requests

if len(sys.argv) < 3:
    print("Usage: python check_cors_headers.py <url> <origin>")
    sys.exit(1)

url = sys.argv[1]
origin = sys.argv[2]

print(f"\nTesting OPTIONS (preflight) request to: {url}")
headers = {
    "Origin": origin,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type, authorization, x-csrftoken"
}
try:
    resp = requests.options(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    for h in [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Credentials",
        "Access-Control-Max-Age"
    ]:
        print(f"{h}: {resp.headers.get(h, 'NOT PRESENT')}")
except Exception as e:
    print(f"Error: {e}")

print(f"\nTesting actual POST request to: {url}")
try:
    resp = requests.post(url, headers={"Origin": origin, "Content-Type": "application/json"}, json={}, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Access-Control-Allow-Origin: {resp.headers.get('Access-Control-Allow-Origin', 'NOT PRESENT')}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
