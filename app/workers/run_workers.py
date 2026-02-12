import multiprocessing
import signal
import sys
import time

from app.tasks.kafka_order_item_worker import run_order_item_kafka_worker
from app.tasks.kafka_order_worker import run_order_kafka_worker


# =========================
# CONFIG SCALE HERE
# =========================
ORDER_ITEM_WORKERS = 7
ORDER_WORKERS = 7
# =========================


processes = []


def start_workers(worker_type: str, count: int, target_func):
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
    print(f"\n[MAIN] Received signal {signum}. Shutting down...", flush=True)

    for p in processes:
        if p.is_alive():
            print(f"[MAIN] Terminating {p.name} (PID={p.pid})", flush=True)
            p.terminate()

    for p in processes:
        p.join()

    print("[MAIN] All workers stopped.")
    sys.exit(0)


def main():
    print("\n========== STARTING WORKERS ==========")
    print(f"OrderItem Workers: {ORDER_ITEM_WORKERS}")
    print(f"Order Workers:     {ORDER_WORKERS}")
    print("======================================\n")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if ORDER_ITEM_WORKERS > 0:
        start_workers(
            worker_type="OrderItemWorker",
            count=ORDER_ITEM_WORKERS,
            target_func=run_order_item_kafka_worker
        )

    if ORDER_WORKERS > 0:
        start_workers(
            worker_type="OrderWorker",
            count=ORDER_WORKERS,
            target_func=run_order_kafka_worker
        )

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
