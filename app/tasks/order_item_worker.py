from app.models.order import OrderItem
from app.models.product import Product
from app.enums import OrderItemStatus
from app.extensions import db
import time


RETRY_LIMIT = 5
SLEEP_NO_JOB = 2
RETRY_DELAY = 0.1


def claim_order_item():
    rows = (
        db.session.query(OrderItem)
        .filter(OrderItem.status == OrderItemStatus.PENDING)
        .order_by(OrderItem.id)
        .limit(1)
        .update(
            {OrderItem.status: OrderItemStatus.PROCESSING},
            synchronize_session=False
        )
    )

    db.session.commit()

    if rows == 0:
        return None

    return (
        OrderItem.query
        .filter(OrderItem.status == OrderItemStatus.PROCESSING)
        .order_by(OrderItem.id)
        .first()
    )


def process_order_item(order_item) -> bool:

    for _ in range(RETRY_LIMIT):

        product = Product.query.get(order_item.product_id)

        if not product:
            return False

        rows = (
            db.session.query(Product)
            .filter(
                Product.id == product.id,
                Product.stock_quantity >= order_item.quantity,
                Product.version == product.version
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


def finalize_order_item(order_item_id, success):

    new_status = (
        OrderItemStatus.RESERVED
        if success
        else OrderItemStatus.FAILED
    )

    (
        db.session.query(OrderItem)
        .filter(
            OrderItem.id == order_item_id,
            OrderItem.status == OrderItemStatus.PROCESSING
        )
        .update(
            {OrderItem.status: new_status},
            synchronize_session=False
        )
    )

    db.session.commit()


def order_item_worker():

    print("OrderItemWorker started...")

    while True:

        try:

            order_item = claim_order_item()

            if not order_item:
                time.sleep(SLEEP_NO_JOB)
                continue

            print(f"Processing OrderItem {order_item.id}")

            success = process_order_item(order_item)

            finalize_order_item(order_item.id, success)

            if success:
                print(f"OrderItem {order_item.id} RESERVED")
            else:
                print(f"OrderItem {order_item.id} FAILED")

        except Exception as e:
            db.session.rollback()
            print("Worker error:", e)
            time.sleep(1)
