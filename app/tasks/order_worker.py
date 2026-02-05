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



SLEEP_NO_JOB = 3
PROCESSING_TIMEOUT = timedelta(minutes=2)

def claim_order():
    now = datetime.utcnow()

    has_pending_items = (
        db.session.query(OrderItem.id)
        .filter(
            OrderItem.order_id == Order.id,
            OrderItem.status == OrderItemStatus.PENDING
        )
        .exists()
    )

    order = (
        db.session.query(Order)
        .filter(
            not_(has_pending_items),
            or_(
                Order.status == OrderStatus.PENDING,
                and_(
                    Order.status == OrderStatus.PROCESSING,
                    Order.processing_at < now - PROCESSING_TIMEOUT
                )
            )
        )
        .order_by(Order.id)
        .with_for_update(skip_locked=True)
        .first()
    )
    return order

def has_failed_item(order_id: str):
    return db.session.query(OrderItem.id).filter(
        OrderItem.order_id == order_id,
        OrderItem.status == OrderItemStatus.FAILED
    ).first() is not None


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

    for item in items:
        product = (
            db.session.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )
        product.stock_quantity += item.quantity


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

            if has_failed_item(order.id):
                process_failed(order)
                print(f"[Order {order.id}] FAILED")
            else:
                process_success(order)
                print(f"[Order {order.id}] COMPLETED")

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