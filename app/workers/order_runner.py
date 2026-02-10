from app import create_app
from app.tasks.order_worker import order_worker

def run_order_worker():
    import os, multiprocessing
    print(
        f"[BOOT] {multiprocessing.current_process().name} "
        f"PID={os.getpid()}",
        flush=True
    )

    app = create_app()
    with app.app_context():
        order_worker()