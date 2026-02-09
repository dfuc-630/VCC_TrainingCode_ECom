#!/usr/bin/env python3
"""
Script tạo 1000 orders với đa luồng và tự động login
Chạy: python create_orders.py
"""

import requests
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ========== CONFIGURATION - CHỈNH SỬA Ở ĐÂY ==========
API_BASE_URL = "http://127.0.0.1:5000/api/v1"
USERNAME = "username5"
PASSWORD = "password123"

TOTAL_ORDERS = 5000
WORKERS = 10

# Product IDs từ database của bạn
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
    "667f3d85-fd64-4817-9841-4edd9ca15c21",
    "5453afd3-af4b-43d8-bd11-03da38cecd96",
    "d51a8ef3-7540-42f3-ac4b-417ee0975e01",
    "1942ce57-7c77-4977-b48f-bac9f299dadd",
    "72839bcc-67c7-4f30-8cca-45de272485ed",
    "2170797a-099d-424b-8c83-d1b0b646bcb4",
    "d513ff6d-f055-4e75-a2f1-2708b0b1c562",
    "825519ec-80fd-4e9a-bad9-fbe8670def2c",
    "9f819fbf-07d4-497f-93db-cda32fa4b73f",
    "4cac6912-2e78-42e0-8220-4f982612845c",
]
# ====================================================


def get_access_token():
    """Login và lấy JWT access token"""
    print("🔐 Đang login để lấy access token...")
    
    login_url = f"{API_BASE_URL}/auth/login"
    
    try:
        response = requests.post(
            login_url,
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ Login thành công!")
                return token
            else:
                print("❌ Không tìm thấy access_token trong response")
                print(f"Response: {response.text}")
                return None
        else:
            print(f"❌ Login thất bại với status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi khi login: {str(e)}")
        return None


def build_order_payload(index):
    """Tạo payload cho order với 1-10 products ngẫu nhiên"""
    num_products = random.randint(1, 10)
    
    items = []
    for _ in range(num_products):
        product_id = random.choice(PRODUCT_IDS)
        quantity = random.randint(1, 3)
        items.append({
            "product_id": product_id,
            "quantity": quantity,
        })

    return {
        "items": items,
        "shipping_address": f"Test Address #{index}",
        "shipping_phone": "0123456789",
    }


def create_single_order(index, headers):
    """Tạo 1 order"""
    start_time = datetime.utcnow()
    order_url = f"{API_BASE_URL}/customer/orders"

    try:
        response = requests.post(
            order_url,
            headers=headers,
            json=build_order_payload(index),
            timeout=10,
        )
    except Exception as e:
        return {
            "index": index,
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
            "index": index,
            "success": True,
            "order_id": data["order"]["id"],
            "status_code": response.status_code,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": duration_ms,
        }

    return {
        "index": index,
        "success": False,
        "status_code": response.status_code,
        "response": response.text,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_ms": duration_ms,
    }


def main():
    print("="*70)
    print("LOAD TEST - TẠO 1000 ORDERS")
    print("="*70)
    
    # Bước 1: Login và lấy token
    access_token = get_access_token()
    if not access_token:
        print("\n❌ Không thể tiếp tục nếu không có access token. Thoát.")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Bước 2: Tạo orders với đa luồng
    print(f"\n🚀 Bắt đầu tạo {TOTAL_ORDERS} orders với {WORKERS} workers...")
    print(f"   Mỗi order có 1-10 products ngẫu nhiên")
    
    all_results = []
    global_start = datetime.utcnow()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [
            executor.submit(create_single_order, i, headers) 
            for i in range(TOTAL_ORDERS)
        ]

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            all_results.append(result)
            completed += 1
            
            if completed % 100 == 0:
                print(f"   Progress: {completed}/{TOTAL_ORDERS} orders")

    global_end = datetime.utcnow()

    # Bước 3: Tính toán thống kê
    success_count = sum(1 for r in all_results if r["success"])
    failed_count = TOTAL_ORDERS - success_count
    total_duration_ms = (global_end - global_start).total_seconds() * 1000
    
    successful_results = [r for r in all_results if r["success"] and r["duration_ms"]]
    if successful_results:
        avg_duration_ms = sum(r["duration_ms"] for r in successful_results) / len(successful_results)
        min_duration_ms = min(r["duration_ms"] for r in successful_results)
        max_duration_ms = max(r["duration_ms"] for r in successful_results)
    else:
        avg_duration_ms = min_duration_ms = max_duration_ms = 0

    # Bước 4: Lưu kết quả đầy đủ
    summary = {
        "total_orders": TOTAL_ORDERS,
        "workers": WORKERS,
        "started_at": global_start.isoformat(),
        "finished_at": global_end.isoformat(),
        "total_duration_ms": total_duration_ms,
        "total_duration_seconds": total_duration_ms / 1000,
        "statistics": {
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round((success_count / TOTAL_ORDERS) * 100, 2),
            "avg_duration_ms": round(avg_duration_ms, 2),
            "min_duration_ms": round(min_duration_ms, 2),
            "max_duration_ms": round(max_duration_ms, 2),
            "throughput_orders_per_second": round(TOTAL_ORDERS / (total_duration_ms / 1000), 2)
        },
        "results": all_results,
    }

    with open("orders_raw_result.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Bước 5: Lưu order IDs để script 2 check
    order_ids_data = [
        {
            "order_id": r["order_id"],
            "created_at": r["start_time"]
        }
        for r in all_results if r["success"]
    ]
    
    with open("order_ids.json", "w", encoding="utf-8") as f:
        json.dump(order_ids_data, f, indent=2, ensure_ascii=False)

    # Bước 6: Hiển thị tóm tắt
    print(f"\n{'='*70}")
    print(f"{'KẾT QUẢ TẠO ORDERS':^70}")
    print(f"{'='*70}")
    print(f"Tổng orders:              {TOTAL_ORDERS}")
    print(f"Thành công:               {success_count} ({summary['statistics']['success_rate']}%)")
    print(f"Thất bại:                 {failed_count}")
    print(f"")
    print(f"Tổng thời gian:           {summary['total_duration_seconds']:.2f} giây")
    print(f"Thời gian TB/order:       {avg_duration_ms:.2f} ms")
    print(f"Thời gian MIN:            {min_duration_ms:.2f} ms")
    print(f"Thời gian MAX:            {max_duration_ms:.2f} ms")
    print(f"Throughput:               {summary['statistics']['throughput_orders_per_second']:.2f} orders/giây")
    print(f"{'='*70}")
    print(f"\n✅ Kết quả chi tiết: orders_raw_result.json")
    print(f"✅ Order IDs để check: order_ids.json")
    print(f"\n➡️  Bây giờ chạy script 2 để check kết quả từ database")


if __name__ == "__main__":
    main()