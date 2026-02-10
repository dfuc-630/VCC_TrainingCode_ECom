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
from app.extensions import db
from sqlalchemy.orm.exc import StaleDataError

SLEEP_NO_JOB = 3
PROCESSING_TIMEOUT = timedelta(minutes=2)
MAX_RETRY = 5
def now():
    return datetime.utcnow()

def claim_order():
    # Check for pending items
    has_pending_items = exists(
        select(1).where(
            OrderItem.order_id == Order.id,
            OrderItem.status == OrderItemStatus.PENDING
        )
    )
    
    # Check for processing items that haven't timed out yet
    # (items that are still being processed by order_item_worker)
    has_active_processing_items = exists(
        select(1).where(
            OrderItem.order_id == Order.id,
            OrderItem.status == OrderItemStatus.PROCESSING,
            or_(
                OrderItem.processing_at.is_(None),
                OrderItem.processing_at >= now() - PROCESSING_TIMEOUT
            )
        )
    )

    order = (
        db.session.query(Order)
        .filter(
            Order.retry_count < MAX_RETRY,
            not_(has_pending_items),
            not_(has_active_processing_items),  # Don't claim if items are still being processed
            # Don't claim orders that are already in final status
            ~Order.status.in_([OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]),
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

def cleanup_stuck_orders():
    """Cleanup orders that have exceeded retry limit but aren't in final status"""
    stuck_orders = (
        db.session.query(Order)
        .filter(
            Order.retry_count >= MAX_RETRY,
            ~Order.status.in_([OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED])
        )
        .with_for_update(skip_locked=True)
        .all()
    )
    
    for order in stuck_orders:
        print(f"Cleaning up stuck order {order.id} with retry_count={order.retry_count}, status={order.status}")
        try:
            process_failed(order)
            db.session.commit()
            print(f"Successfully cleaned up order {order.id}")
        except Exception as e:
            db.session.rollback()
            # Last resort: mark as FAILED directly
            order.status = OrderStatus.FAILED
            order.payment_status = PaymentStatus.UNPAID
            db.session.commit()
            print(f"Force marked order {order.id} as FAILED due to cleanup error: {e}")

def lock_order_items(order_id):
    return (
        db.session.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .with_for_update()
        .all()
    )

def mark_order_failed_permanently(order, error: Exception):
    order.retry_count += 1
    order.last_error = str(error)

    if order.retry_count >= MAX_RETRY:
        print(f"Order {order.id} exceeded retry limit ({order.retry_count}/{MAX_RETRY}), marking FAILED")
        try:
            process_failed(order)
            print("done process_failed")
        except Exception as e:
            # If process_failed fails, at least mark order as FAILED
            print(f"process_failed raised exception: {e}, marking order as FAILED directly")
            order.status = OrderStatus.FAILED
            order.payment_status = PaymentStatus.UNPAID
    else:
        print(f"Order {order.id} retry {order.retry_count}/{MAX_RETRY}, resetting to PENDING")
        order.status = OrderStatus.PENDING
        order.processing_at = None

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
    if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
        print(f"Order {order.id} already in final status {order.status}, skipping process_success")
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

    updated_count = db.session.query(OrderItem).filter(
        OrderItem.order_id == order.id,
        OrderItem.status == OrderItemStatus.RESERVED
    ).update(
        {OrderItem.status: OrderItemStatus.COMPLETED},
        synchronize_session=False
    )
    print(f"Updated {updated_count} items to COMPLETED")

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
    if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
        print(f"Order {order.id} already in final status {order.status}, skipping process_failed")
        return

    rollback_stock(order.id)
    print("has restock product")
    
    # Update all items to CANCELLED (except already final statuses)
    # Only rollback stock for RESERVED items, but cancel all non-final items
    updated_count = db.session.query(OrderItem).filter(
        OrderItem.order_id == order.id,
        ~OrderItem.status.in_([OrderItemStatus.CANCELLED, OrderItemStatus.COMPLETED])
    ).update(
        {OrderItem.status: OrderItemStatus.CANCELLED},
        synchronize_session=False
    )
    print(f"Updated {updated_count} items to CANCELLED")

    # Use CANCELLED status for orders that failed processing
    order.status = OrderStatus.CANCELLED
    order.payment_status = PaymentStatus.UNPAID
    print(f"order.status set to CANCELLED: {order.status}")

def order_worker():
    print("OrderWorker started")
    print("WORKER DB =", db.engine.url)
    order = None
    cleanup_counter = 0
    while True:
        try:
            # Periodically cleanup stuck orders (every 100 iterations)
            cleanup_counter += 1
            if cleanup_counter >= 100:
                cleanup_counter = 0
                try:
                    cleanup_stuck_orders()
                except Exception as e:
                    print(f"Cleanup stuck orders error (non-fatal): {e}")
            
            order = claim_order()
    
            if not order:
                time.sleep(SLEEP_NO_JOB)
                continue

            db.session.commit()

            items = lock_order_items(order.id)
            if not items:
                raise Exception("Order has no items")
            statuses = {i.status for i in items}
            
            # Log statuses for debugging
            status_list = [s.value for s in statuses]
            print(f"Order {order.id} items statuses: {status_list}")

            # Check if all items are already in final status but order is not
            # This can happen if process_success/process_failed partially completed
            if statuses <= {OrderItemStatus.COMPLETED}:
                # All items are COMPLETED, order should be COMPLETED too
                if order.status != OrderStatus.COMPLETED:
                    print(f"Order {order.id} has all items COMPLETED but order status is {order.status}, fixing...")
                    order.status = OrderStatus.COMPLETED
                    order.payment_status = PaymentStatus.PAID
                    db.session.commit()
                    print("order fixed to COMPLETED")
                    continue
                else:
                    # Already completed, skip
                    print(f"Order {order.id} already COMPLETED, skipping")
                    continue
            
            # Check if any item is CANCELLED → set order to CANCELLED
            # Priority: CANCELLED > FAILED > other statuses
            elif OrderItemStatus.CANCELLED in statuses:
                if order.status not in [OrderStatus.CANCELLED, OrderStatus.FAILED]:
                    cancelled_count = sum(1 for i in items if i.status == OrderItemStatus.CANCELLED)
                    print(f"Order {order.id} has {cancelled_count} CANCELLED item(s) but order status is {order.status}, fixing...")
                    order.status = OrderStatus.CANCELLED
                    order.payment_status = PaymentStatus.UNPAID
                    db.session.commit()
                    print("order fixed to CANCELLED")
                    continue
                else:
                    # Already cancelled/failed, skip
                    print(f"Order {order.id} already CANCELLED/FAILED, skipping")
                    continue

            # Check for failed items
            elif OrderItemStatus.FAILED in statuses:
                process_failed(order)
                print("order failed")

            # Check if all items are reserved (ready for payment)
            elif statuses <= {OrderItemStatus.RESERVED}:
                process_success(order)
                print("order success")

            # Check if there are processing items that have timed out
            # These should be treated as failed
            elif OrderItemStatus.PROCESSING in statuses:
                processing_items = [i for i in items if i.status == OrderItemStatus.PROCESSING]
                timed_out_items = [
                    i for i in processing_items 
                    if i.processing_at and (now() - i.processing_at) > PROCESSING_TIMEOUT
                ]
                
                if timed_out_items:
                    # Items have timed out, mark them as failed
                    print(f"Order {order.id} has {len(timed_out_items)} timed out processing items")
                    for item in timed_out_items:
                        item.status = OrderItemStatus.FAILED
                    db.session.commit()
                    # Re-lock and re-check statuses after marking failed
                    items = lock_order_items(order.id)
                    statuses = {i.status for i in items}
                    if OrderItemStatus.FAILED in statuses:
                        process_failed(order)
                        print("order failed after timeout")
                    else:
                        raise Exception(f"Order {order.id} has mixed statuses after timeout handling: {statuses}")
                else:
                    # Items are still processing (shouldn't happen due to claim_order check, but handle it)
                    print(f"Order {order.id} has active processing items, releasing back to pending")
                    order.status = OrderStatus.PENDING
                    order.processing_at = None
                    db.session.commit()
                    continue

            else:
                # Unknown status combination - log detailed info
                status_details = {}
                for item in items:
                    status = item.status.value
                    if status not in status_details:
                        status_details[status] = []
                    status_details[status].append(item.id)
                
                error_msg = f"Order {order.id} has unfinished items with statuses: {status_list}. Details: {status_details}"
                print(error_msg)
                raise Exception(error_msg)

            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            print("Idempotent conflict, safe to ignore")
        except StaleDataError:
            db.session.rollback()
            print("Optimistic lock hit - order already handled")
        except Exception as e:
            db.session.rollback()
            if order:
                try:
                    mark_order_failed_permanently(order, e)
                    print("mark_order_failed_permanently")
                    db.session.commit()
                    print("done commit")
                except Exception as inner:
                    db.session.rollback()
                    print("Retry handling failed:", inner)

            print("OrderWorker error:", e)
            time.sleep(1)
