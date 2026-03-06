#!/usr/bin/env python
"""
Test script to verify login endpoint is working
Just test login with existing user
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_login():
    """Test login with existing user"""
    
    # Test login with existing user
    print("Testing login with existing user...")
    login_data = {
        "email": "testuser@example.com",
        "password": "SecurePass123!"
    }
    
    login_response = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data
    )
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {json.dumps(login_response.json(), indent=2)}\n")
    
    if login_response.status_code == 200:
        print("✅ Login successful!")
        return login_response.json()
    else:
        print("❌ Login failed!")
        return None
    
    # Test with wrong password
    print("\nTesting with wrong password...")
    login_data_wrong = {
        "email": "testuser@example.com",
        "password": "WrongPassword123!"
    }
    
    login_response_wrong = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data_wrong
    )
    print(f"Login (Wrong Password) Status: {login_response_wrong.status_code}")
    print(f"Login (Wrong Password) Response: {json.dumps(login_response_wrong.json(), indent=2)}\n")
    
    # Test with non-existent user
    print("Testing with non-existent user...")
    login_data_nonexist = {
        "email": "nonexistent@example.com",
        "password": "AnyPassword123!"
    }
    
    login_response_nonexist = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data_nonexist
    )
    print(f"Login (Non-existent) Status: {login_response_nonexist.status_code}")
    print(f"Login (Non-existent) Response: {json.dumps(login_response_nonexist.json(), indent=2)}\n")

if __name__ == "__main__":
    test_login()
