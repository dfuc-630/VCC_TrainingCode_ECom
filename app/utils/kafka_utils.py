from confluent_kafka import Producer
import json
from kafka import KafkaProducer
import time
from app.services.kafka_producer_order_service import get_kafka_producer
kafka_producer = get_kafka_producer()

def order_item_producer_send(order):
     for item in order.items:
        kafka_producer.send(
            topic="order-item-events",
            key=str(item.product_id),
            value={
                "order_id": order.id,
                "order_item_id": item.id
            }
        )


def send_order_item_event(order_item, order_id):
    print("order_item_id: ", order_item.id)
    success = kafka_producer.publish_order_item_event(
        order_item_id=order_item.id,
        order_id=order_id,
        product_id=order_item.product_id,
        quantity=order_item.quantity,
        event_type="PROCESS_ITEM"
    )
    
    if not success:
        print(
            f"Failed to publish event for order_item {order_item.id}. "
            "Item will not be processed unless manually retriggered."
        )

    # kafka_producer.flush() 