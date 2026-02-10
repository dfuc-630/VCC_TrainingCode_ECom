#!/usr/bin/env python3
"""
Script debug order bị stuck
Chạy: python debug_stuck_order.py
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.order import Order, OrderItem
from app.enums import OrderStatus, OrderItemStatus

# ========== CONFIGURATION ==========
DATABASE_URL = "postgresql+psycopg2://flask_user:Phuc06032004%40@localhost:5432/flask_db_new"
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

def analyze_stuck_orders():
    """Phân tích các orders bị stuck"""
    session = get_db_session()
    
    try:
        # Tìm các orders không ở trạng thái cuối cùng
        stuck_orders = (
            session.query(Order)
            .filter(
                ~Order.status.in_([
                    OrderStatus.COMPLETED,
                    OrderStatus.CANCELLED,
                ])
            )
            .all()
        )
        
        print(f"\n{'='*80}")
        print(f"Tìm thấy {len(stuck_orders)} orders không ở trạng thái cuối cùng")
        print(f"{'='*80}\n")
        
        for order in stuck_orders:
            print(f"\n{'─'*80}")
            print(f"Order ID: {order.id}")
            print(f"Order Number: {order.order_number}")
            print(f"Status: {order.status.value}")
            print(f"Payment Status: {order.payment_status.value}")
            print(f"Retry Count: {order.retry_count}")
            print(f"Processing At: {order.processing_at}")
            print(f"Last Error: {order.last_error}")
            print(f"Created At: {order.created_at}")
            
            # Lấy tất cả items
            items = session.query(OrderItem).filter(
                OrderItem.order_id == order.id
            ).all()
            
            print(f"\nItems ({len(items)}):")
            item_statuses = {}
            for item in items:
                status = item.status.value
                item_statuses[status] = item_statuses.get(status, 0) + 1
                print(f"  - Item {item.id}: {status} (processing_at: {item.processing_at})")
            
            print(f"\nItem Status Summary: {item_statuses}")
            
            # Phân tích tại sao order không được claim
            print(f"\nPhân tích:")
            
            # 1. Check retry_count
            if order.retry_count >= 5:
                print(f"  ❌ Retry count >= 5: Order sẽ không được claim nữa")
            
            # 2. Check pending items
            pending_items = [i for i in items if i.status == OrderItemStatus.PENDING]
            if pending_items:
                print(f"  ❌ Có {len(pending_items)} pending items: Order sẽ không được claim")
            
            # 3. Check processing items (có thể bị stuck)
            processing_items = [i for i in items if i.status == OrderItemStatus.PROCESSING]
            if processing_items:
                from datetime import datetime, timedelta
                timeout = timedelta(minutes=2)
                now = datetime.utcnow()
                stuck_processing = [
                    i for i in processing_items 
                    if i.processing_at and (now - i.processing_at) > timeout
                ]
                if stuck_processing:
                    print(f"  ⚠️  Có {len(stuck_processing)} processing items bị timeout (>2 phút)")
                else:
                    print(f"  ℹ️  Có {len(processing_items)} processing items (chưa timeout)")
            
            # 4. Check các status không được xử lý
            valid_statuses = {OrderItemStatus.RESERVED, OrderItemStatus.FAILED}
            item_status_set = {i.status for i in items}
            invalid_statuses = item_status_set - valid_statuses - {OrderItemStatus.PENDING, OrderItemStatus.PROCESSING}
            if invalid_statuses:
                print(f"  ⚠️  Có items ở status không được xử lý: {[s.value for s in invalid_statuses]}")
            
            # 5. Check logic claim
            has_pending = any(i.status == OrderItemStatus.PENDING for i in items)
            all_reserved = all(i.status == OrderItemStatus.RESERVED for i in items) if items else False
            has_failed = any(i.status == OrderItemStatus.FAILED for i in items)
            all_completed = all(i.status == OrderItemStatus.COMPLETED for i in items) if items else False
            all_cancelled = all(i.status == OrderItemStatus.CANCELLED for i in items) if items else False
            
            print(f"\n  Logic claim_order():")
            print(f"    - retry_count < 5: {order.retry_count < 5}")
            print(f"    - Không có pending items: {not has_pending}")
            print(f"    - Không ở final status: {order.status not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]}")
            print(f"    - Status hợp lệ: {order.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]}")
            
            if order.status == OrderStatus.PROCESSING:
                from datetime import datetime, timedelta
                timeout = timedelta(minutes=2)
                now = datetime.utcnow()
                if order.processing_at:
                    is_timeout = (now - order.processing_at) > timeout
                    print(f"    - Processing timeout: {is_timeout}")
            
            print(f"\n  Logic order_worker():")
            print(f"    - Có failed items: {has_failed}")
            print(f"    - Tất cả reserved: {all_reserved}")
            print(f"    - Tất cả completed: {all_completed}")
            print(f"    - Tất cả cancelled: {all_cancelled}")
            print(f"    - Statuses: {[s.value for s in item_status_set]}")
            
            has_cancelled = any(i.status == OrderItemStatus.CANCELLED for i in items)
            
            if all_completed:
                print(f"    → Sẽ fix order status to COMPLETED")
            elif has_cancelled:
                print(f"    → Sẽ fix order status to CANCELLED (có ít nhất 1 item CANCELLED)")
            elif has_failed:
                print(f"    → Sẽ gọi process_failed()")
            elif all_reserved:
                print(f"    → Sẽ gọi process_success()")
            else:
                print(f"    → Sẽ raise Exception 'Order has unfinished items'")
        
        print(f"\n{'='*80}\n")
        
    finally:
        session.close()

if __name__ == "__main__":
    analyze_stuck_orders()
