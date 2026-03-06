#!/usr/bin/env python
"""
Test script to verify wallet creation and balance retrieval
"""

import requests
import json
from uuid import uuid4

BASE_URL = "http://127.0.0.1:5000/api/v1"

def test_wallet_flow():
    """Test complete wallet flow: register -> login -> check wallet balance -> deposit"""
    
    email = f"testuser{uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"
    
    # Step 1: Register a user
    print("1. Registering new user...")
    register_data = {
        "email": email,
        "password": password,
        "full_name": "Test User",
        "phone": "0987654321",
        "role": "customer"
    }
    
    register_response = requests.post(
        f"{BASE_URL}/users/register",
        json=register_data
    )
    print(f"Register Status: {register_response.status_code}")
    register_result = register_response.json()
    print(f"Register Response: {json.dumps(register_result, indent=2)}\n")
    
    if register_response.status_code != 201:
        print("❌ Registration failed!")
        return
    
    user_id = register_result['user_id']
    
    # Step 2: Login
    print("2. Logging in...")
    login_data = {
        "email": email,
        "password": password
    }
    
    login_response = requests.post(
        f"{BASE_URL}/users/login",
        json=login_data
    )
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {json.dumps(login_response.json(), indent=2)}\n")
    
    if login_response.status_code != 200:
        print("❌ Login failed!")
        return
    
    # Step 3: Get wallet balance
    print("3. Getting wallet balance...")
    balance_response = requests.get(
        f"{BASE_URL}/wallet/{user_id}/balance"
    )
    print(f"Balance Status: {balance_response.status_code}")
    print(f"Balance Response: {json.dumps(balance_response.json(), indent=2)}\n")
    
    if balance_response.status_code != 200:
        print("❌ Failed to get wallet balance!")
        return
    
    print("✅ Wallet balance retrieved successfully!")
    
    # Step 4: Deposit money
    print("\n4. Depositing money to wallet...")
    deposit_data = {
        "amount": 100000,
        "currency": "VND"
    }
    
    deposit_response = requests.post(
        f"{BASE_URL}/wallet/{user_id}/deposit",
        json=deposit_data
    )
    print(f"Deposit Status: {deposit_response.status_code}")
    print(f"Deposit Response: {json.dumps(deposit_response.json(), indent=2)}\n")
    
    if deposit_response.status_code == 200:
        print("✅ Deposit successful!")
    else:
        print("❌ Deposit failed!")
    
    # Step 5: Check new balance
    print("\n5. Checking new wallet balance...")
    balance_response2 = requests.get(
        f"{BASE_URL}/wallet/{user_id}/balance"
    )
    print(f"New Balance Status: {balance_response2.status_code}")
    print(f"New Balance Response: {json.dumps(balance_response2.json(), indent=2)}\n")

if __name__ == "__main__":
    test_wallet_flow()
