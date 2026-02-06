import requests
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

API_URL = "http://localhost:5000/api/v1/customer/orders"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3MDM1NDIwMiwianRpIjoiMGU4NDgwODctM2JmZC00ZDkxLWJkOTItYTBjY2RlMjM1MTI2IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIyNGNjODE1LWRkYzctNDdjMS04MDIzLTFkYTI5YjdkZmM0MiIsIm5iZiI6MTc3MDM1NDIwMiwiY3NyZiI6IjYxMjI5NzE5LTJiZTQtNDRlMS1hOGMzLWI1OTY5MGU0NWMzMCIsImV4cCI6MTc3MDM1NTEwMn0.3dcLg6MVtru6-drHktoInz3qTm3cKARJL1dD8EOB51w"

TOTAL_ORDERS = 1000
WORKERS = 10
OUTPUT_FILE = "orders_raw_result.json"

HEADERS = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
}

# ===== PRODUCT IDS (lấy từ data bạn gửi) =====
PRODUCT_IDS = [
    "e11d4c3e-2d95-44fb-94d8-8bfdaa4abf46",
    "d19542a1-39a0-4b11-b628-ff71198bca51",
    "b777dd2c-efb5-43f3-be8a-8111283d06e5",
    "361949f8-5a80-4ff4-bfc8-93bbbf72c40c",
    "a04d0a3d-2cac-4900-b400-9826c22b270e",
    "c9dbfc9f-9b74-479b-8e78-a3ca0e07a119",
    "bd80ed7f-3334-46de-9bc2-1c23d934946e",
    "95a6e344-dd57-4840-b39d-21fc5c493960",
    "2c778261-f7f7-45f5-8a0c-d4702563dba2",
    "6a6bb28f-9240-4cd0-93a2-62a8fe50f90a",
]

def build_payload(i):
    product_id = random.choice(PRODUCT_IDS)

    return {
        "items": [
            {
                "product_id": product_id,
                "quantity": random.randint(1, 3),
            }
        ],
        "shipping_address": f"Test Address #{i}",
        "shipping_phone": "0123456789",
    }

def create_order(i):
    start_time = datetime.utcnow()

    try:
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=build_payload(i),
            timeout=10,
        )
    except Exception as e:
        return {
            "index": i,
            "success": False,
            "error": str(e),
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration_ms": None,
        }

    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    if response.status_code == 201:
        data = response.json()
        return {
            "index": i,
            "success": True,
            "order_id": data["order"]["id"],
            "status_code": response.status_code,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": duration_ms,
        }

    return {
        "index": i,
        "success": False,
        "status_code": response.status_code,
        "response": response.text,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_ms": duration_ms,
    }

def main():
    print(f"🚀 Creating {TOTAL_ORDERS} orders with {WORKERS} workers...")
    all_results = []

    global_start = datetime.utcnow()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(create_order, i) for i in range(TOTAL_ORDERS)]

        for future in as_completed(futures):
            all_results.append(future.result())

    global_end = datetime.utcnow()

    summary = {
        "total_orders": TOTAL_ORDERS,
        "workers": WORKERS,
        "started_at": global_start.isoformat(),
        "finished_at": global_end.isoformat(),
        "total_duration_ms": (global_end - global_start).total_seconds() * 1000,
        "results": all_results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    success_count = sum(1 for r in all_results if r["success"])
    print(f"✅ Done. Success: {success_count}/{TOTAL_ORDERS}")
    print(f"📄 Raw result saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
