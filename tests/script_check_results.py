#!/usr/bin/env python3
"""
Script check kết quả orders từ database
Chạy: python check_results.py
"""

import json
import time
import csv
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import model - đảm bảo đường dẫn đúng với project của bạn
from app.models.order import Order
from app.enums import OrderStatus

# ========== CONFIGURATION - CHỈNH SỬA Ở ĐÂY ==========
DATABASE_URL = "postgresql://flask_user:Phuc06032004%40@localhost:5432/flask_db"
POLL_INTERVAL = 0.5  # giây giữa các lần check
# ====================================================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

def get_db_session():
    """Tạo database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def monitor_orders(orders, session):
    """Poll database cho đến khi tất cả orders hoàn thành"""
    print(f"📊 Bắt đầu monitor {len(orders)} orders...")
    
    finished = []
    start_all = datetime.utcnow()
    
    pending_orders = {o["order_id"]: o for o in orders}
    check_count = 0

    while pending_orders:
        for order_id in list(pending_orders.keys()):
            order = session.get(Order, order_id)
            
            if order and order.status in [OrderStatus.COMPLETED.value, OrderStatus.FAILED.value]:
                finished_at = datetime.utcnow()
                created_at = datetime.fromisoformat(pending_orders[order_id]["created_at"])
                
                finished.append({
                    "order_id": order_id,
                    "status": order.status,
                    "created_at": created_at.isoformat(),
                    "finished_at": finished_at.isoformat(),
                    "duration_ms": (finished_at - created_at).total_seconds() * 1000
                })
                
                del pending_orders[order_id]
                
                if len(finished) % 100 == 0:
                    print(f"   Progress: {len(finished)}/{len(orders)} orders hoàn thành")
        
        check_count += 1
        if check_count % 20 == 0:
            print(f"   Đang chờ {len(pending_orders)} orders...")
        
        time.sleep(POLL_INTERVAL)
    
    end_all = datetime.utcnow()
    
    print(f"✅ Tất cả orders đã hoàn thành!")
    return finished, start_all, end_all


def calculate_statistics(results, start_time, end_time):
    """Tính toán thống kê chi tiết"""
    total = len(results)
    success = sum(1 for r in results if r["status"] == "completed")
    failed = total - success
    
    total_time_ms = (end_time - start_time).total_seconds() * 1000
    total_time_seconds = total_time_ms / 1000
    
    durations = [r["duration_ms"] for r in results]
    avg_time_ms = sum(durations) / total if total > 0 else 0
    min_time_ms = min(durations) if durations else 0
    max_time_ms = max(durations) if durations else 0
    
    # Tính percentiles
    sorted_durations = sorted(durations)
    p50 = sorted_durations[int(len(sorted_durations) * 0.50)] if sorted_durations else 0
    p90 = sorted_durations[int(len(sorted_durations) * 0.90)] if sorted_durations else 0
    p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
    p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0
    
    return {
        "total_orders": total,
        "success_count": success,
        "failed_count": failed,
        "success_rate": round((success / total * 100), 2) if total > 0 else 0,
        "total_time_ms": round(total_time_ms, 2),
        "total_time_seconds": round(total_time_seconds, 2),
        "avg_time_ms": round(avg_time_ms, 2),
        "min_time_ms": round(min_time_ms, 2),
        "max_time_ms": round(max_time_ms, 2),
        "median_time_ms": round(p50, 2),
        "p90_time_ms": round(p90, 2),
        "p95_time_ms": round(p95, 2),
        "p99_time_ms": round(p99, 2),
        "throughput_orders_per_second": round(total / total_time_seconds, 2) if total_time_seconds > 0 else 0
    }


def export_csv(results, stats):
    """Xuất kết quả ra CSV"""
    filename = "order_report.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["KẾT QUẢ XỬ LÝ ORDERS"])
        writer.writerow([])
        
        # Chi tiết từng order
        writer.writerow(["order_id", "status", "duration_ms", "created_at", "finished_at"])
        for r in results:
            writer.writerow([
                r["order_id"],
                r["status"],
                round(r["duration_ms"], 2),
                r["created_at"],
                r["finished_at"]
            ])
        
        # Thống kê tóm tắt
        writer.writerow([])
        writer.writerow(["THỐNG KÊ TỔNG HỢP"])
        writer.writerow([])
        writer.writerow(["Chỉ số", "Giá trị"])
        writer.writerow(["Tổng số orders", stats["total_orders"]])
        writer.writerow(["Số orders thành công", stats["success_count"]])
        writer.writerow(["Số orders thất bại", stats["failed_count"]])
        writer.writerow(["Tỷ lệ thành công (%)", stats["success_rate"]])
        writer.writerow([])
        writer.writerow(["Tổng thời gian (giây)", stats["total_time_seconds"]])
        writer.writerow(["Tổng thời gian (ms)", stats["total_time_ms"]])
        writer.writerow([])
        writer.writerow(["Thời gian TB/order (ms)", stats["avg_time_ms"]])
        writer.writerow(["Thời gian MIN (ms)", stats["min_time_ms"]])
        writer.writerow(["Thời gian MAX (ms)", stats["max_time_ms"]])
        writer.writerow(["Median - P50 (ms)", stats["median_time_ms"]])
        writer.writerow(["P90 (ms)", stats["p90_time_ms"]])
        writer.writerow(["P95 (ms)", stats["p95_time_ms"]])
        writer.writerow(["P99 (ms)", stats["p99_time_ms"]])
        writer.writerow([])
        writer.writerow(["Throughput (orders/giây)", stats["throughput_orders_per_second"]])
    
    print(f"✅ CSV report: {filename}")


def export_json(results, stats, start_time, end_time):
    """Xuất kết quả ra JSON"""
    filename = "order_report.json"
    
    report = {
        "started_at": start_time.isoformat(),
        "finished_at": end_time.isoformat(),
        "statistics": stats,
        "results": results
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON report: {filename}")


def print_summary(stats):
    """In tóm tắt ra console"""
    print(f"\n{'='*70}")
    print(f"{'KẾT QUẢ XỬ LÝ ORDERS':^70}")
    print(f"{'='*70}")
    print(f"Tổng số orders:           {stats['total_orders']}")
    print(f"Thành công:               {stats['success_count']} ({stats['success_rate']}%)")
    print(f"Thất bại:                 {stats['failed_count']}")
    print(f"")
    print(f"Tổng thời gian:           {stats['total_time_seconds']:.2f} giây")
    print(f"Thời gian TB/order:       {stats['avg_time_ms']:.2f} ms")
    print(f"Thời gian MIN:            {stats['min_time_ms']:.2f} ms")
    print(f"Thời gian MAX:            {stats['max_time_ms']:.2f} ms")
    print(f"Median (P50):             {stats['median_time_ms']:.2f} ms")
    print(f"P90:                      {stats['p90_time_ms']:.2f} ms")
    print(f"P95:                      {stats['p95_time_ms']:.2f} ms")
    print(f"P99:                      {stats['p99_time_ms']:.2f} ms")
    print(f"")
    print(f"Throughput:               {stats['throughput_orders_per_second']:.2f} orders/giây")
    print(f"{'='*70}")


def main():
    print("="*70)
    print("CHECK KẾT QUẢ ORDERS TỪ DATABASE")
    print("="*70)
    
    input_file = os.path.join(PROJECT_ROOT, "order_ids.json")

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            orders = json.load(f)
        print(f"✅ Đã load {len(orders)} orders từ {input_file}")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {input_file}")
        print("   Vui lòng chạy create_orders.py trước!")
        return
    except json.JSONDecodeError:
        print(f"❌ File {input_file} không phải JSON hợp lệ")
        return


    # Bước 1: Load order IDs
    input_file = "order_ids.json"
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            orders = json.load(f)
        print(f"✅ Đã load {len(orders)} orders từ {input_file}")
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {input_file}")
        print("   Vui lòng chạy create_orders.py trước!")
        return
    except Exception as e:
        print(f"❌ Lỗi khi đọc {input_file}: {str(e)}")
        return
    
    if not orders:
        print("❌ Không có orders nào trong file!")
        return
    
    # Bước 2: Kết nối database
    try:
        session = get_db_session()
        print("✅ Đã kết nối database")
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {str(e)}")
        print(f"   Kiểm tra lại DATABASE_URL")
        return
    
    # Bước 3: Monitor orders cho đến khi hoàn thành
    try:
        finished, start_time, end_time = monitor_orders(orders, session)
    except KeyboardInterrupt:
        print("\n⚠️  Đã dừng bởi người dùng")
        session.close()
        return
    except Exception as e:
        print(f"❌ Lỗi khi monitor: {str(e)}")
        session.close()
        return
    finally:
        session.close()
    
    # Bước 4: Tính toán thống kê
    stats = calculate_statistics(finished, start_time, end_time)
    
    # Bước 5: Xuất kết quả
    export_csv(finished, stats)
    export_json(finished, stats, start_time, end_time)
    
    # Bước 6: In tóm tắt
    print_summary(stats)


if __name__ == "__main__":
    main()