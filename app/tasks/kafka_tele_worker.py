import json
import logging
from app.extensions import db
from app.models.order import Order
from kafka import KafkaConsumer
from app.utils.send_tele_message import send_tele_message

logger = logging.getLogger(__name__)

from app import create_app

def run_tele_kafka_worker(worker_id: int):
    app = create_app()

    with app.app_context():
        consumer = KafkaConsumer(
            'tele-noti-events',
            bootstrap_servers=['10.5.68.163:9092'],
            group_id='tele-notification-group',
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        logger.info(f"TeleWorker-{worker_id} started, consuming 'tele-noti-events'...")

        for msg in consumer:
            try:
                data = msg.value
                order_id = data.get("order_id")
                order = db.session.query(Order).filter_by(id=order_id).first()

                if not order:
                    logger.warning(f"Order {order_id} not found")
                    continue
                
                if order.sent_tele is False:
                    order = (
                        db.session.query(Order)
                        .filter(Order.id == order_id, Order.sent_tele == False)
                        .with_for_update()
                        .first()
                    )

                    if not order:
                        continue
                    
                    order.sent_tele = True
                    db.session.commit()
                    
                    send_tele_message(
                        order_id=data.get("order_id"),
                        status=data.get("status", True),
                        message=data.get("custom_message")
                    )
                    
                        
                logger.info(f"TeleWorker-{worker_id} processed Order: {data.get('order_id')}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"TeleWorker-{worker_id} error: {e}")