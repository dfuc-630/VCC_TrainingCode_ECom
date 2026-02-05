from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.wallet import Wallet, WalletTransaction
from app.enums import OrderStatus, OrderItemStatus, PaymentStatus, TransactionType
from app.extensions import db
from app.services.wallet_service import WalletService
from decimal import Decimal
import time
from sqlalchemy import update, and_, or_, not_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from sqlalchemy import select, exists


SLEEP_NO_JOB = 3
PROCESSING_TIMEOUT = timedelta(minutes=2)
def now():
    return datetime.utcnow()

def claim_order():
    has_pending_items = exists(
        select(1).where(
            OrderItem.order_id == Order.id,
            OrderItem.status == OrderItemStatus.PENDING
        )
    )

    order = (
        db.session.query(Order)
        .filter(
            not_(has_pending_items),
            or_(
                Order.status == OrderStatus.PENDING,
                and_(
                    Order.status == OrderStatus.PROCESSING,
                    Order.processing_at < now() - PROCESSING_TIMEOUT
                )
            )
        )
        .order_by(Order.processing_at.nullsfirst(), Order.id)
        .with_for_update(skip_locked=True)
        .first()
    )
    if not order:
        return None
    order.status = OrderStatus.PROCESSING
    order.processing_at = now()
    
    return order

def lock_order_items(order_id):
    return (
        db.session.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .with_for_update()
        .all()
    )

def has_failed_item(order_id: str):
    return (
        db.session.query(OrderItem.id)
        .filter(
            OrderItem.order_id == order_id,
            OrderItem.status == OrderItemStatus.FAILED
        )
        .with_for_update()
        .first()
        is not None
    )


def lock_wallets(order):
    wallet_ids = sorted([
        order.customer.wallet.id,
        order.seller.wallet.id
    ])

    wallets = (
        db.session.query(Wallet)
        .filter(Wallet.id.in_(wallet_ids))
        .with_for_update()
        .all()
    )

    return {w.id: w for w in wallets}


def process_success(order):
    if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED]:
        return

    wallets = lock_wallets(order)

    WalletService.deduct_atomic(
        wallet=wallets[order.customer.wallet.id],
        amount=order.total_amount,
        order_id=order.id,
        description=f"Payment for order {order.order_number}"
    )

    WalletService.deposit_atomic(
        wallet=wallets[order.seller.wallet.id],
        amount=order.total_amount,
        order_id=order.id,
        description=f"Income from order {order.order_number}"
    )

    db.session.query(OrderItem).filter(
        OrderItem.order_id == order.id,
        OrderItem.status == OrderItemStatus.RESERVED
    ).update(
        {OrderItem.status: OrderItemStatus.SUCCESS},
        synchronize_session=False
    )

    order.status = OrderStatus.COMPLETED
    order.payment_status = PaymentStatus.PAID


def rollback_stock(order_id: str):
    items = db.session.query(OrderItem).filter(
        OrderItem.order_id == order_id,
        OrderItem.status == OrderItemStatus.RESERVED
    ).all()

    product_ids = sorted({i.product_id for i in items})
    products = (
        db.session.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )

    product_map = {p.id: p for p in products}

    for item in items:
        product_map[item.product_id].stock_quantity += item.quantity


def process_failed(order):
    if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED]:
        return

    rollback_stock(order.id)

    db.session.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).update(
        {OrderItem.status: OrderItemStatus.CANCELLED},
        synchronize_session=False
    )

    order.status = OrderStatus.FAILED
    order.payment_status = PaymentStatus.FAILED


def order_worker():
    print("OrderWorker started")

    while True:
        try:
            order = claim_order()
    
            if not order:
                time.sleep(SLEEP_NO_JOB)
                continue

            db.session.commit()

            items = lock_order_items(order.id)
            statuses = {i.status for i in items}

            if OrderItemStatus.FAILED in statuses:
                process_failed(order)

            elif statuses <= {OrderItemStatus.RESERVED}:
                process_success(order)

            else:
                raise Exception("Order has unfinished items")

            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            print("Idempotent conflict, safe to ignore")

        except Exception as e:
            db.session.rollback()
            print("OrderWorker error:", e)
            time.sleep(1)

from app import create_app
app = create_app()

with app.app_context():
    order_worker()