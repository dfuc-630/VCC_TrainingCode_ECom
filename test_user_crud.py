#!/usr/bin/env python
"""Test user registration and retrieval"""
import requests
import time

time.sleep(2)

# Test user registration
print("Test 1: Register user")
r = requests.post("http://localhost:5000/api/v1/users/register",
    json={"email": f"test{int(time.time())}@test.com", "password": "BobPassword123", "full_name": "Bob Smith"}, timeout=5)
print(f"Status: {r.status_code}")

if r.status_code == 201:
    data = r.json()
    user_id = data.get("user_id")
    print(f"User ID: {user_id}")
    
    print("\nTest 2: Get user by ID")
    time.sleep(0.5)
    r2 = requests.get(f"http://localhost:5000/api/v1/users/{user_id}", timeout=5)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        email = r2.json().get("email")
        print(f"✓ SUCCESS! Retrieved user: {email}")
    else:
        print(f"✗ Failed to get user: {r2.text[:100]}")
else:
    print(f"✗ Registration failed: {r.text}")
