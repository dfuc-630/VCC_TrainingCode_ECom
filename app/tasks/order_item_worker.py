from app.models.order import OrderItem
from app.models.product import Product
from app.enums import OrderItemStatus
from app.extensions import db
import time


RETRY_LIMIT = 5
SLEEP_NO_JOB = 2
RETRY_DELAY = 0.1


def claim_order_item():
    item = (
        db.session.query(OrderItem)
        .filter(OrderItem.status == OrderItemStatus.PENDING)
        .order_by(OrderItem.id)
        .with_for_update(skip_locked=True)
        .first()
    )

    if not item:
        return None

    item.status = OrderItemStatus.PROCESSING
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
    order_item.status = (
        OrderItemStatus.RESERVED if success else OrderItemStatus.FAILED
    )


def order_item_worker():

    print("OrderItemWorker started...")

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

from app import create_app
app = create_app()

with app.app_context():
    order_item_worker()