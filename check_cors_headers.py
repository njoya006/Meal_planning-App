#!/usr/bin/env python3
"""
Check CORS headers for a given endpoint and origin.
Usage: python check_cors_headers.py <url> <origin> [payload_json]
Example: python check_cors_headers.py https://your-aws-hostname/api/users/login/ https://www.chopsmo.site '{"email": "demo@example.com", "password": "wrong"}'
"""
import json
import sys
import requests

if len(sys.argv) < 3:
    print("Usage: python check_cors_headers.py <url> <origin> [payload_json]")
    sys.exit(1)

url = sys.argv[1]
origin = sys.argv[2]
if len(sys.argv) >= 4:
    try:
        payload = json.loads(sys.argv[3])
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON payload provided: {exc}")
        sys.exit(1)
else:
    payload = {
        "email": "placeholder@example.com",
        "password": "invalid-password"
    }

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
    resp = requests.post(
        url,
        headers={"Origin": origin, "Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        timeout=10
    )
    print(f"Status: {resp.status_code}")
    print(f"Access-Control-Allow-Origin: {resp.headers.get('Access-Control-Allow-Origin', 'NOT PRESENT')}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
