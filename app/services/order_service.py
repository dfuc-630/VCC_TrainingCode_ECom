from typing import Any


from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.extensions import db
from app.utils.helpers import generate_order_number
from decimal import Decimal
from app.enums import OrderStatus, PaymentStatus, OrderItemStatus
from sqlalchemy import or_
from flask import jsonify
from app.utils.order_utils import _get_products_for_update, _validate_items, _create_order, _create_order_items
from app.services.kafka_producer_order_service import get_kafka_producer
from app.utils.kafka_utils import send_order_item_event

class OrderService:
    @staticmethod
    def create_order(customer_id, items_data, shipping_address, shipping_phone) -> Order:
        if not items_data:
            raise ValueError("Order must have at least one item")

        product_ids = list({item["product_id"] for item in items_data})

        try:
            products_map = _get_products_for_update(product_ids)

            if len(products_map) != len(product_ids):
                raise ValueError("One or more products not found")

            wallet = WalletService.get_wallet_by_user_id(customer_id)
            if not wallet:
                raise ValueError("Wallet not found")

            validated_items, seller_id, total_amount = _validate_items(items_data, products_map)

            order = _create_order(
                customer_id,
                seller_id,
                total_amount,
                shipping_address,
                shipping_phone
            )

            order_items = _create_order_items(order, validated_items)
            # logger.info(f"Published {len(order_items)} events to Kafka for order {order.id}")
            db.session.commit()
            for item in order_items:
                send_order_item_event(item, order.id)
            return order

        except Exception as e:
            db.session.rollback()
            print(f"Failed to create order: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_order_by_id(order_id: str, user_id: str = None, role: str = None) -> Order:
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")

        # Access control
        if role == "customer" and order.customer_id != user_id:
            raise ValueError("Order not found")
        elif role == "seller" and order.seller_id != user_id:
            raise ValueError("Order not found")

        return order

    @staticmethod
    def get_orders(user_id: str = None, role: str = None, status: str = None, page: int = 1, per_page: int = 20,):
        query = Order.query

        if role == "customer":
            query = query.filter_by(customer_id=user_id)
        elif role == "seller":
            query = query.filter_by(seller_id=user_id)

        if status:
            query = query.filter_by(status=status)

        return query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def update_order_status(order_id: str, seller_id: str, new_status: str) -> Order:
        """Update order status (seller only)"""
        order = Order.query.filter_by(id=order_id, seller_id=seller_id).first()
        if not order:
            raise ValueError("Order not found")

        # Validate status transition
        allowed_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.SHIPPING, OrderStatus.CANCELLED],
            OrderStatus.SHIPPING: [OrderStatus.COMPLETED],
        }

        if (
            order.status not in allowed_transitions
            or new_status not in allowed_transitions[order.status]
        ):
            raise ValueError(f"Cannot transition from {order.status} to {new_status}")

        order.status = new_status
        db.session.commit()

        return order

    @staticmethod
    def cancel_order(order_id: str, customer_id: str) -> Order:
        """Cancel order and refund"""
        try:
            order = Order.query.filter_by(id=order_id, customer_id=customer_id).with_for_update().first()
            if not order:
                raise ValueError("Order not found")

            if not order.can_cancel():
                raise ValueError("Order cannot be cancelled")

            # Update order status
            if order.status == OrderStatus.CANCELLED:
                raise ValueError("Order already cancelled")
            if order.payment_status == PaymentStatus.REFUNDED:
                raise ValueError("Order already refunded")

            order.status = OrderStatus.CANCELLED

            # Restore stock
            product_ids = sorted(item.product_id for item in order.items)
            products = (
                db.session.query(Product)
                .filter(Product.id.in_(product_ids))
                .order_by(Product.id.asc())
                .with_for_update()
                .all()
            )

            products_map = {p.id: p for p in products}

            for item in order.items:
                products_map[item.product_id].stock_quantity += item.quantity

            # Refund to wallet
            if order.payment_status == PaymentStatus.PAID:
                wallet = WalletService.get_wallet_by_user_id(customer_id)
                WalletService.refund(
                    wallet.id,
                    order.total_amount,
                    order.id,
                    f"Refund for cancelled order {order.order_number}",
                    commit = False # ensure only 1 commit
                )
                order.payment_status = PaymentStatus.REFUNDED

            db.session.commit()
            return order

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def retry_failed_order(order_id: str) -> bool:
        """
        Retry a failed order by republishing events for FAILED items
        
        Args:
            order_id: Order ID to retry
            
        Returns:
            True if events were published successfully
        """
        kafka_producer = get_kafka_producer()
        
        try:
            order = db.session.query(Order).filter(Order.id == order_id).first()
            if not order:
                print(f"Order {order_id} not found")
                return False
            
            # Get failed items
            failed_items = (
                db.session.query(OrderItem)
                .filter(
                    OrderItem.order_id == order_id,
                    OrderItem.status == OrderItemStatus.FAILED
                )
                .all()
            )
            
            if not failed_items:
                print(f"No failed items found for order {order_id}")
                return True
            
            # Reset order status
            order.status = OrderStatus.PENDING
            order.retry_count += 1
            
            # Reset failed items to PENDING
            for item in failed_items:
                item.status = OrderItemStatus.PENDING
            
            db.session.commit()
            
            # Republish events
            for item in failed_items:
                kafka_producer.publish_order_item_event(
                    order_item_id=item.id,
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    event_type="RETRY_ITEM"
                )
            
            kafka_producer.flush()
            
            print(
                f"Retried order {order_id} with {len(failed_items)} items "
                f"(retry_count={order.retry_count})"
            )
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Failed to retry order {order_id}: {e}", exc_info=True)
            return False