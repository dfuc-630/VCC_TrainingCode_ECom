import multiprocessing as mp
import signal
import sys
from app.workers.order_item_runner import run_order_item_worker
from app.workers.order_runner import run_order_worker

ORDER_ITEM_WORKERS = 7
ORDER_WORKERS = 7

processes = []

def start_process(p):
    p.start()
    print(
        f"[SPAWNED] {p.name} PID={p.pid}",
        flush=True
    )

def shutdown(signum, frame):
    print("Shutting down workers...")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    for i in range(ORDER_ITEM_WORKERS):
        p = mp.Process(
            target=run_order_item_worker,
            name=f"OrderItemWorker-{i+1}"
        )
        start_process(p)
        processes.append(p)

    for i in range(ORDER_WORKERS):
        p = mp.Process(
            target=run_order_worker,
            name=f"OrderWorker-{i+1}"
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
