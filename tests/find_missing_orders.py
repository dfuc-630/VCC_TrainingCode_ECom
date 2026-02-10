#!/usr/bin/env python3
"""
Script tìm các order_id trong order_ids.json nhưng không tồn tại trong database
Chạy: python find_missing_orders.py
"""

import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.order import Order

# ========== CONFIGURATION ==========
DATABASE_URL = "postgresql://flask_user:Phuc06032004%40@localhost:5432/flask_db"
ORDER_IDS_FILE = "order_ids.json"
# ===================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

def get_db_session():
    """Tạo database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def find_missing_orders():
    """Tìm các order_id không tồn tại trong database"""
    # Load order_ids.json
    order_ids_path = os.path.join(PROJECT_ROOT, ORDER_IDS_FILE)
    
    try:
        with open(order_ids_path, "r", encoding="utf-8") as f:
            order_data = json.load(f)
        print(f"✅ Đã load {len(order_data)} orders từ {ORDER_IDS_FILE}")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {order_ids_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ File {order_ids_path} không phải JSON hợp lệ")
        return
    
    # Kết nối database
    session = get_db_session()
    
    try:
        missing_orders = []
        existing_orders = []
        
        print(f"\n🔍 Đang kiểm tra {len(order_data)} orders...")
        
        for idx, order_info in enumerate(order_data):
            order_id = order_info.get("order_id")
            if not order_id:
                print(f"⚠️ Entry {idx} không có order_id")
                continue
            
            # Query database
            order = session.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                missing_orders.append(order_info)
                if len(missing_orders) <= 10:  # Chỉ in 10 đầu tiên
                    print(f"   ❌ Order {order_id} không tồn tại trong DB")
            else:
                existing_orders.append(order_id)
            
            if (idx + 1) % 1000 == 0:
                print(f"   Đã kiểm tra {idx + 1}/{len(order_data)} orders...")
        
        print(f"\n{'='*80}")
        print(f"KẾT QUẢ KIỂM TRA")
        print(f"{'='*80}")
        print(f"Tổng số orders trong file:     {len(order_data)}")
        print(f"Số orders tồn tại trong DB:   {len(existing_orders)}")
        print(f"Số orders KHÔNG tồn tại:      {len(missing_orders)}")
        print(f"{'='*80}\n")
        
        if missing_orders:
            print(f"📋 Danh sách {min(20, len(missing_orders))} orders đầu tiên không tồn tại:")
            for i, order_info in enumerate(missing_orders[:20]):
                print(f"   {i+1}. {order_info.get('order_id')} (created_at: {order_info.get('created_at', 'N/A')})")
            
            if len(missing_orders) > 20:
                print(f"   ... và {len(missing_orders) - 20} orders khác")
            
            # Lưu vào file
            missing_file = "missing_orders.json"
            with open(missing_file, "w", encoding="utf-8") as f:
                json.dump(missing_orders, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Đã lưu danh sách vào {missing_file}")
        else:
            print("✅ Tất cả orders đều tồn tại trong database!")
        
    finally:
        session.close()

if __name__ == "__main__":
    find_missing_orders()
