from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers="10.5.68.163:9092",
    key_serializer=lambda k: k.encode("utf-8"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
    retries=3
)

event = {
    "order_id": 1002,
    "order_item_id": 55502,
    "product_id": 100,
    "quantity": 1,
    "action": "RESERVE_STOCK",
    "created_at": int(time.time())
}

future = producer.send(
    topic="order-item-events",
    key=str(event["order_item_id"]),
    value=event
)

result = future.get(timeout=10)
print("Send OK")
print("Topic:", result.topic)
print("Partition:", result.partition)
print("Offset:", result.offset)

producer.flush()
producer.close()
