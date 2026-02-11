from kafka import KafkaConsumer
import json
import os

consumer = KafkaConsumer(
    "order-item-events",
    bootstrap_servers="10.5.68.163:9092",
    group_id="order-item-worker-group",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

print("Worker PID:", os.getpid())

for msg in consumer:
    print(
        f"Worker {os.getpid()} | "
        f"Partition {msg.partition} | "
        f"Offset {msg.offset} | "
        f"OrderItem {msg.value['order_item_id']}"
    )
