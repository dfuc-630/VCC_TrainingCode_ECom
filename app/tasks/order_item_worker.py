from datetime import timedelta, datetime
import multiprocessing
import os
from app.models.order import OrderItem
from app.models.product import Product
from app.enums import OrderItemStatus
from app.extensions import db
import time
from sqlalchemy import update, and_, or_, not_


RETRY_LIMIT = 5
SLEEP_NO_JOB = 2
RETRY_DELAY = 0.1
PROCESSING_TIMEOUT = timedelta(minutes=2)
def now():
    return datetime.utcnow()

def claim_order_item():
    item = (
        db.session.query(OrderItem)
        .filter(
            or_(
                OrderItem.status == OrderItemStatus.PENDING,
                and_(
                    OrderItem.status == OrderItemStatus.PROCESSING,
                    OrderItem.processing_at < now() - PROCESSING_TIMEOUT
                )
            )
        )
        .order_by(OrderItem.processing_at.nullsfirst(), OrderItem.id)
        .with_for_update(skip_locked=True)
        .first()
    )

    if not item:
        return None

    item.status = OrderItemStatus.PROCESSING
    item.processing_at = now()
    db.session.commit()

    return item

def try_reserve_stock(order_item) -> bool:
    for _ in range(RETRY_LIMIT):

        product = (
            db.session.query(Product)
            .filter(Product.id == order_item.product_id)
            .first()
        )

        if not product:
            return False

        if product.stock_quantity < order_item.quantity:
            return False

        rows = (
            db.session.query(Product)
            .filter(
                Product.id == product.id,
                Product.version == product.version,
                Product.stock_quantity >= order_item.quantity
            )
            .update(
                {
                    Product.stock_quantity: Product.stock_quantity - order_item.quantity,
                    Product.version: Product.version + 1
                },
                synchronize_session=False
            )
        )

        if rows == 1:
            return True

        db.session.rollback()
        time.sleep(RETRY_DELAY)

    return False


def finalize_order_item(order_item, success: bool):
    if order_item.status in [OrderItemStatus.RESERVED, OrderItemStatus.FAILED]:
        return
    order_item.status = (
        OrderItemStatus.RESERVED if success else OrderItemStatus.FAILED
    )


def order_item_worker():

    print(
        f"[START] {multiprocessing.current_process().name} "
        f"PID={os.getpid()}",
        flush=True
    )

    while True:
        try:
            order_item = claim_order_item()

            if not order_item:
                time.sleep(SLEEP_NO_JOB)
                continue
            print(f"[OrderItem {order_item.id}] processing")

            success = try_reserve_stock(order_item)

            finalize_order_item(order_item, success)

            if success:
                print(f"[OrderItem {order_item.id}] RESERVED")
            else:
                print(f"[OrderItem {order_item.id}] FAILED")
            
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print("OrderItemWorker error:", e)
            time.sleep(1)
