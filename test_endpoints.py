#!/usr/bin/env python
"""Quick endpoint tests"""
import requests
import time
import json

time.sleep(1)

base_url = "http://localhost:5000/api/v1"

tests = [
    ("GET", "/users/email/test@example.com", None, "Get user by email"),
    ("POST", "/products", {"seller_id": "seller-1", "sku": "SKU-001", "name": "Test Product", "price": 99.99}, "Create product"),
    ("POST", "/wallet/user-1/deposit", {"amount": 100}, "Deposit to wallet"),
]

print("\n" + "="*50)
print("ENDPOINT TESTS")
print("="*50 + "\n")

for method, path, payload, desc in tests:
    try:
        url = base_url + path
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=payload, timeout=5)
        
        status_icon = "✓" if r.status_code < 400 else "✗"
        print(f"{status_icon} {method:6} {path:40} → {r.status_code}")
        
    except Exception as e:
        print(f"✗ {method:6} {path:40} → Error: {str(e)[:50]}")

print("\n" + "="*50 + "\n")
