import requests
import random
from decimal import Decimal
from faker import Faker

fake = Faker()

API_URL = "http://localhost:5000/api/v1/seller/products"  # sửa theo base url của bạn
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3MDY5OTk0NywianRpIjoiY2MwNTAzNmMtNjAzMy00MGM2LWI3NDUtNjdjYTQ5Zjg1YTMxIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImUyNTNhMjI4LTQ1MGItNDJkZS1iOWJmLWM0NjZhMjBlNTg3NCIsIm5iZiI6MTc3MDY5OTk0NywiY3NyZiI6ImZhMWZkN2I4LTQ4NjctNDlhMC04MTNlLTRlMDY4NmI1YTk0YSIsImV4cCI6MTc3MDcwMDg0N30.VPHYReSnxsyF5l7SgLTt7m32HmUhJzJSxKVmktr0Oyc"

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
}

CATEGORY_IDS = [
    "electronics",
    "fashion",
    "books",
    "home",
    "other",
]

def generate_product(index):
    current_price = round(random.uniform(10, 500), 2)
    original_price = round(current_price + random.uniform(5, 100), 2)

    return {
        "name": f"Test Product {index} - {fake.word()}",
        "description": fake.sentence(),
        "detail": fake.text(max_nb_chars=200),
        "category_id": random.choice(CATEGORY_IDS),
        "original_price": str(original_price),
        "current_price": str(current_price),
        "stock_quantity": random.randint(0, 100),
        "image_url": fake.image_url(),
    }

def main():
    success = 0
    fail = 0

    for i in range(1, 101):
        payload = generate_product(i)
        response = requests.post(API_URL, json=payload, headers=HEADERS)

        if response.status_code == 201:
            success += 1
            print(f"[OK] Created product {i}")
        else:
            fail += 1
            print(f"[FAIL] Product {i} | {response.status_code} | {response.text}")

    print("---- RESULT ----")
    print(f"Success: {success}")
    print(f"Fail   : {fail}")

if __name__ == "__main__":
    main()
