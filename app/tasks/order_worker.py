from app.models.order import Order, OrderItem
from app.models.product import Product
from app.enums import OrderStatus, OrderItemStatus, PaymentStatus
from app.extensions import db
from app.services.wallet_service import WalletService
from decimal import Decimal
import time


SLEEP_NO_JOB = 3


def claim_order():

    rows = (
        db.session.query(Order)
        .filter(Order.status == OrderStatus.PENDING)
        .order_by(Order.id)
        .limit(1)
        .update(
            {Order.status: OrderStatus.PROCESSING},
            synchronize_session=False
        )
    )

    db.session.commit()

    if rows == 0:
        return None

    return (
        Order.query
        .filter(Order.status == OrderStatus.PROCESSING)
        .order_by(Order.id)
        .first()
    )


def order_items_ready(order):

    pending_count = (
        db.session.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id,
            OrderItem.status == OrderItemStatus.PENDING
        )
        .count()
    )

    return pending_count == 0


def has_failed_item(order):

    failed_count = (
        db.session.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id,
            OrderItem.status == OrderItemStatus.FAILED
        )
        .count()
    )

    return failed_count > 0


def process_success_order(order):

    WalletService.deduct(
        wallet_id=order.customer.wallet.id,
        amount=order.total_amount,
        order_id=order.id,
        description=f"Payment for order {order.order_number}",
        commit=False
    )

    seller_wallet = order.seller.wallet

    if not seller_wallet:
        raise Exception("Seller wallet not found")

    seller_wallet.add_balance(order.total_amount)

    (
        db.session.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id,
            OrderItem.status == OrderItemStatus.RESERVED
        )
        .update(
            {OrderItem.status: OrderItemStatus.SUCCESS},
            synchronize_session=False
        )
    )

    order.status = OrderStatus.COMPLETED
    order.payment_status = PaymentStatus.PAID


def rollback_reserved_stock(order):

    reserved_items = (
        OrderItem.query
        .filter(
            OrderItem.order_id == order.id,
            OrderItem.status == OrderItemStatus.RESERVED
        )
        .all()
    )

    product_ids = sorted({i.product_id for i in reserved_items})

    products = (
        db.session.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )

    products_map = {p.id: p for p in products}

    for item in reserved_items:
        products_map[item.product_id].stock_quantity += item.quantity


def process_failed_order(order):

    rollback_reserved_stock(order)

    (
        db.session.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .update(
            {OrderItem.status: OrderItemStatus.CANCELLED},
            synchronize_session=False
        )
    )

    order.status = OrderStatus.FAILED


def order_worker():

    print("OrderWorker started...")

    while True:

        try:

            order = claim_order()

            if not order:
                time.sleep(SLEEP_NO_JOB)
                continue

            print(f"Processing Order {order.id}")

            if not order_items_ready(order):
                order.status = OrderStatus.PENDING
                db.session.commit()
                time.sleep(1)
                continue

            if has_failed_item(order):
                process_failed_order(order)
                print(f"Order {order.id} FAILED")
            else:
                process_success_order(order)
                print(f"Order {order.id} COMPLETED")

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print("OrderWorker error:", e)
            time.sleep(1)
