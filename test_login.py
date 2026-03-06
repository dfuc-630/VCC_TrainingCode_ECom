#!/usr/bin/env python
"""
Test script to verify login endpoint is working
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_login_flow():
    """Test complete login flow: register -> login"""
    
    # Step 1: Register a user
    print("1. Registering new user...")
    register_data = {
        "email": "testuser@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User",
        "phone": "0987654321",
        "role": "customer"
    }
    
    register_response = requests.post(
        f"{BASE_URL}/users/register",
        json=register_data
    )
    print(f"Register Status: {register_response.status_code}")
    print(f"Register Response: {register_response.json()}\n")
    
    if register_response.status_code != 201:
        print("❌ Registration failed!")
        return
    
    # Step 2: Login with registered user
    print("2. Logging in with registered user...")
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
    
    # Step 3: Test with wrong password
    print("3. Testing with wrong password...")
    login_data_wrong = {
        "email": "testuser@example.com",
        "password": "WrongPassword123!"
    }
    
    login_response_wrong = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data_wrong
    )
    print(f"Login (Wrong Password) Status: {login_response_wrong.status_code}")
    print(f"Login (Wrong Password) Response: {login_response_wrong.json()}\n")
    
    # Step 4: Test with non-existent user
    print("4. Testing with non-existent user...")
    login_data_nonexist = {
        "email": "nonexistent@example.com",
        "password": "AnyPassword123!"
    }
    
    login_response_nonexist = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data_nonexist
    )
    print(f"Login (Non-existent) Status: {login_response_nonexist.status_code}")
    print(f"Login (Non-existent) Response: {login_response_nonexist.json()}\n")

if __name__ == "__main__":
    test_login_flow()
