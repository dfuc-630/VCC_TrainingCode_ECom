import json
import time
import csv
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.order import Order
from app.enums import OrderStatus

DATABASE_URL = "postgresql://user:password@localhost:5432/yourdb"
POLL_INTERVAL = 0.5

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def main():
    with open("order_ids.json") as f:
        orders = json.load(f)

    session = Session()

    finished = []
    start_all = datetime.utcnow()

    print("Waiting for worker to finish orders...")

    for o in orders:
        order_id = o["order_id"]
        created_at = datetime.fromisoformat(o["created_at"])

        while True:
            order = session.get(Order, order_id)
            if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED]:
                finished_at = datetime.utcnow()
                finished.append({
                    "order_id": order_id,
                    "status": order.status.value,
                    "duration_ms": (finished_at - created_at).total_seconds() * 1000
                })
                break
            time.sleep(POLL_INTERVAL)

    session.close()
    end_all = datetime.utcnow()

    export_csv(finished, start_all, end_all)


def export_csv(results, start_all, end_all):
    total = len(results)
    success = sum(1 for r in results if r["status"] == "COMPLETED")
    failed = total - success

    total_time_ms = (end_all - start_all).total_seconds() * 1000
    avg_time_ms = sum(r["duration_ms"] for r in results) / total

    with open("order_report.csv", "w", newline="") as f:
        w = csv.writer(f)

        w.writerow(["order_id", "status", "duration_ms"])
        for r in results:
            w.writerow([r["order_id"], r["status"], round(r["duration_ms"], 2)])

        w.writerow([])
        w.writerow(["TOTAL_ORDERS", total])
        w.writerow(["SUCCESS", success])
        w.writerow(["FAILED", failed])
        w.writerow(["SUCCESS_RATE", round(success / total * 100, 2)])
        w.writerow(["TOTAL_TIME_MS", round(total_time_ms, 2)])
        w.writerow(["AVG_TIME_MS", round(avg_time_ms, 2)])

    print("Report saved to order_report.csv")


if __name__ == "__main__":
    main()
