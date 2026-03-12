"""
DDD Workers Runner
Starts DDD-based Kafka workers for order processing
"""
import multiprocessing
import signal
import sys
import time

from ddd.order_management.infrastructure.workers.ddd_order_item_worker import run_ddd_order_item_kafka_worker
from ddd.order_management.infrastructure.workers.ddd_order_worker import run_ddd_order_kafka_worker


# =========================
# CONFIG SCALE HERE
# =========================
DDD_ORDER_ITEM_WORKERS = 7
DDD_ORDER_WORKERS = 7
# =========================


processes = []


def start_workers(worker_type: str, count: int, target_func):
    """Start worker processes"""
    for i in range(count):
        p = multiprocessing.Process(
            target=target_func,
            args=(i + 1,),
            name=f"{worker_type}-{i+1}"
        )
        p.start()
        processes.append(p)
        print(f"[SPAWNED] {worker_type}-{i+1} PID={p.pid}", flush=True)


def shutdown(signum, frame):
    """Gracefully shutdown all workers"""
    print(f"\n[MAIN] Received signal {signum}. Shutting down...", flush=True)

    for p in processes:
        if p.is_alive():
            print(f"[MAIN] Terminating {p.name} (PID={p.pid})", flush=True)
            p.terminate()

    for p in processes:
        p.join(timeout=5)
        if p.is_alive():
            print(f"[MAIN] Force killing {p.name} (PID={p.pid})", flush=True)
            p.kill()

    print("[MAIN] All workers stopped.")
    sys.exit(0)


def main():
    print("\n========== STARTING DDD WORKERS ==========")
    print(f"DDD OrderItem Workers: {DDD_ORDER_ITEM_WORKERS}")
    print(f"DDD Order Workers:     {DDD_ORDER_WORKERS}")
    print("==========================================\n")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if DDD_ORDER_ITEM_WORKERS > 0:
        start_workers(
            worker_type="DDDOrderItemWorker",
            count=DDD_ORDER_ITEM_WORKERS,
            target_func=run_ddd_order_item_kafka_worker
        )

    if DDD_ORDER_WORKERS > 0:
        start_workers(
            worker_type="DDDOrderWorker",
            count=DDD_ORDER_WORKERS,
            target_func=run_ddd_order_kafka_worker
        )

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
