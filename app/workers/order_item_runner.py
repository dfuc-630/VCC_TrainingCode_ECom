from app import create_app
from app.tasks.order_item_worker import order_item_worker

def run_order_item_worker():
    import traceback, os, multiprocessing

    try:
        print(
            f"[BOOT] {multiprocessing.current_process().name} "
            f"PID={os.getpid()}",
            flush=True
        )

        app = create_app()
        with app.app_context():
            order_item_worker()

    except Exception:
        print(traceback.format_exc(), flush=True)
        raise
