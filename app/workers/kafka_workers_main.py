"""
Main runner for Hybrid Kafka + DB Polling order processing workers
"""
import multiprocessing as mp
import signal
import sys
import logging

from tasks.kafka_order_item_worker import run_order_item_kafka_worker
from tasks.kafka_order_worker import run_order_kafka_worker
from db_polling_fallback_worker import run_db_polling_fallback_worker
from hybrid_coordinator import get_coordinator, HybridConfig, ProcessingMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Worker configuration
ORDER_ITEM_KAFKA_WORKERS = 7      # Kafka consumers for order-item-events
ORDER_KAFKA_WORKERS = 7            # Kafka consumers for order-item-result
DB_POLLING_FALLBACK_WORKERS = 3    # DB polling workers (only active when Kafka fails)

processes = []


def start_process(p):
    p.start()
    logger.info(f"[SPAWNED] {p.name} PID={p.pid}")


def shutdown(signum, frame):
    logger.info("Shutting down all workers...")
    
    # Stop coordinator first
    coordinator = get_coordinator()
    coordinator.stop()
    
    for p in processes:
        if p.is_alive():
            logger.info(f"Terminating {p.name} (PID={p.pid})")
            p.terminate()
    
    # Wait for all processes to terminate
    for p in processes:
        p.join(timeout=10)
        if p.is_alive():
            logger.warning(f"Force killing {p.name} (PID={p.pid})")
            p.kill()
    
    logger.info("All workers stopped")
    sys.exit(0)


def main():
    # Start coordinator
    coordinator = get_coordinator()
    coordinator.start()
    
    mode_name = HybridConfig.MODE.value
    logger.info(f"Starting order processing workers in {mode_name.upper()} mode...")
    logger.info(
        f"Configuration: {ORDER_ITEM_KAFKA_WORKERS} Kafka item workers, "
        f"{ORDER_KAFKA_WORKERS} Kafka order workers, "
        f"{DB_POLLING_FALLBACK_WORKERS} DB polling fallback workers"
    )
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Start Kafka workers (if not DB_POLLING_ONLY mode)
    if HybridConfig.MODE != ProcessingMode.DB_POLLING_ONLY:
        # Start OrderItem Kafka workers
        for i in range(ORDER_ITEM_KAFKA_WORKERS):
            p = mp.Process(
                target=run_order_item_kafka_worker,
                args=(i + 1,),
                name=f"OrderItemKafkaWorker-{i+1}"
            )
            start_process(p)
            processes.append(p)
        
        # Start Order Kafka workers
        for i in range(ORDER_KAFKA_WORKERS):
            p = mp.Process(
                target=run_order_kafka_worker,
                args=(i + 1,),
                name=f"OrderKafkaWorker-{i+1}"
            )
            start_process(p)
            processes.append(p)
    else:
        logger.info("Skipping Kafka workers (DB_POLLING_ONLY mode)")
    
    # Start DB polling fallback workers (if not KAFKA_ONLY mode)
    if HybridConfig.MODE != ProcessingMode.KAFKA_ONLY:
        for i in range(DB_POLLING_FALLBACK_WORKERS):
            p = mp.Process(
                target=run_db_polling_fallback_worker,
                args=(i + 1,),
                name=f"DBPollingWorker-{i+1}"
            )
            start_process(p)
            processes.append(p)
        
        if HybridConfig.MODE == ProcessingMode.HYBRID:
            logger.info(
                "DB polling workers started in STANDBY mode. "
                "Will activate if Kafka becomes unhealthy."
            )
    else:
        logger.info("Skipping DB polling workers (KAFKA_ONLY mode)")
    
    logger.info(f"All {len(processes)} workers started successfully")
    logger.info(f"Coordinator running with background threads")
    
    # Wait for all processes
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()