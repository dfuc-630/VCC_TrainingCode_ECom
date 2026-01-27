from typing import Any


from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.extensions import db
from app.utils.helpers import generate_order_number
from decimal import Decimal
from app.enums import OrderStatus, PaymentStatus
from sqlalchemy import ord_

class OrderService:
    @staticmethod
    def create_order(customer_id: str, items_data: list, shipping_address: str, shipping_phone: str) -> Order:
        if not items_data:
            raise ValueError("Order must have at least one item")

        product_ids = sorted(list(set[Any](item['product_id'] for item in items_data))) # sort to avoid deadlock
        
        try:
            products_query = (
                db.session.query(Product)
                .filter(Product.id.in_(product_ids))
                .with_for_update()
                .all()
            )
            
            # Change to dictionary for fast get
            products_map = {p.id: p for p in products_query}
            
            if len(products_map) != len(product_ids):
                raise ValueError("One or more products not found")

            # Validate logic
            total_amount = Decimal("0")
            seller_id = None
            validated_items = []

            for item_data in items_data:
                p_id = item_data["product_id"]
                qty = item_data["quantity"]
                product = products_map[p_id]

                if qty <= 0:
                    raise ValueError(f"Invalid quantity for {product.name}")

                if not product.is_active:
                    raise ValueError(f"Product {product.name} is not available")

                if not product.has_stock(qty):
                    raise ValueError(f"Insufficient stock for {product.name}")

                if seller_id is None:
                    seller_id = product.seller_id
                elif seller_id != product.seller_id:
                    raise ValueError("All products must be from the same seller") # Phase 1, can upgrade

                subtotal = product.current_price * qty
                total_amount += subtotal
                
                validated_items.append({
                    "product": product,
                    "quantity": qty,
                    "price": product.current_price,
                    "subtotal": subtotal
                })

            wallet = WalletService.get_wallet_by_user_id(customer_id)
            if not wallet:
                raise ValueError("Wallet not found")

            # Create Order
            order = Order(
                order_number=generate_order_number(),
                customer_id=customer_id,
                seller_id=seller_id,
                total_amount=total_amount,
                shipping_address=shipping_address,
                shipping_phone=shipping_phone,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.UNPAID,
            )
            db.session.add(order)
            db.session.flush()  # Get order.id

            # Create OrderItems và deduct quantity (Atomic Update)
            for item in validated_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item["product"].id,
                    product_name=item["product"].name,
                    price=item["price"],
                    quantity=item["quantity"],
                    subtotal=item["subtotal"],
                )
                db.session.add(order_item)
                
                # direct deduct on locked object
                item["product"].deduct_stock(item["quantity"])

            # Pay
            WalletService.deduct(
                wallet_id=wallet.id,
                amount=total_amount,
                order_id=order.id,
                description=f"Payment for order {order.order_number}",
                commit=False
            )

            order.payment_status = PaymentStatus.PAID
            
            db.session.commit()
            return order

        except Exception as e:
            db.session.rollback()
            # Nên log e ở đây để debug
            raise e

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
            order.status = OrderStatus.CANCELLED

            # Restore stock
            for item in order.items:
                Product.query.filter_by(id=item.product_id).update({"stock": Product.stock + item.quantity}) # direct update
                # item.product.add_stock(item.quantity) # race condition

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
