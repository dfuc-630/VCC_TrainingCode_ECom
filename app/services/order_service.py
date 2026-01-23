from app.models.order import Order, OrderItem
from app.models.product import Product
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.extensions import db
from app.utils.helpers import generate_order_number
from decimal import Decimal
from app.enums import OrderStatus, PaymentStatus


class OrderService:
    """Order service handling order operations"""
    
    @staticmethod
    def create_order(customer_id: str, items_data: list, shipping_address: str, 
                    shipping_phone: str) -> Order:
        """Create new order with transaction"""
        if not items_data:
            raise ValueError('Order must have at least one item')
        
        # Validate and collect items
        order_items = []
        total_amount = Decimal('0')
        seller_id = None
        
        for item_data in items_data:
            product = ProductService.get_product_by_id(item_data['product_id'])
            
            if not product.is_active:
                raise ValueError(f'Product {product.name} is not available')
            
            if not product.has_stock(item_data['quantity']):
                raise ValueError(f'Insufficient stock for {product.name}')
            
            # Ensure all products from same seller
            if seller_id is None:
                seller_id = product.seller_id
            elif seller_id != product.seller_id:
                raise ValueError('All products must be from the same seller')
            
            subtotal = product.current_price * item_data['quantity']
            total_amount += subtotal
            
            order_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'subtotal': subtotal
            })
        
        # Check wallet balance
        wallet = WalletService.get_wallet_by_user_id(customer_id)
        if not wallet.can_deduct(total_amount):
            raise ValueError('Insufficient balance')
        
        # Start transaction
        try:
            # Create order
            order = Order(
                order_number=generate_order_number(),
                customer_id=customer_id,
                seller_id=seller_id,
                total_amount=total_amount,
                shipping_address=shipping_address,
                shipping_phone=shipping_phone,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.UNPAID
            )
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Create order items and deduct stock
            for item_data in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data['product'].id,
                    product_name=item_data['product'].name,
                    price=item_data['product'].current_price,
                    quantity=item_data['quantity'],
                    subtotal=item_data['subtotal']
                )
                db.session.add(order_item)
                
                # Deduct stock
                item_data['product'].deduct_stock(item_data['quantity'])
            
            # Deduct from wallet
            WalletService.deduct(
                wallet.id,
                total_amount,
                order.id,
                f'Payment for order {order.order_number}'
            )
            
            # Update payment status
            order.payment_status = PaymentStatus.PAID
            
            db.session.commit()
            return order
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_order_by_id(order_id: str, user_id: str = None, role: str = None) -> Order:
        """Get order by ID with access control"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError('Order not found')
        
        # Access control
        if role == 'customer' and order.customer_id != user_id:
            raise ValueError('Order not found')
        elif role == 'seller' and order.seller_id != user_id:
            raise ValueError('Order not found')
        
        return order
    
    @staticmethod
    def get_orders(user_id: str = None, role: str = None, status: str = None,
                  page: int = 1, per_page: int = 20):
        """Get orders with filters"""
        query = Order.query
        
        if role == 'customer':
            query = query.filter_by(customer_id=user_id)
        elif role == 'seller':
            query = query.filter_by(seller_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Order.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def update_order_status(order_id: str, seller_id: str, new_status: str) -> Order:
        """Update order status (seller only)"""
        order = Order.query.filter_by(id=order_id, seller_id=seller_id).first()
        if not order:
            raise ValueError('Order not found')
        
        # Validate status transition
        allowed_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.SHIPPING, OrderStatus.CANCELLED],
            OrderStatus.SHIPPING: [OrderStatus.COMPLETED],
        }
        
        if order.status not in allowed_transitions or \
           new_status not in allowed_transitions[order.status]:
            raise ValueError(f'Cannot transition from {order.status} to {new_status}')
        
        order.status = new_status
        db.session.commit()
        
        return order
    
    @staticmethod
    def cancel_order(order_id: str, customer_id: str) -> Order:
        """Cancel order and refund"""
        order = Order.query.filter_by(id=order_id, customer_id=customer_id).first()
        if not order:
            raise ValueError('Order not found')
        
        if not order.can_cancel():
            raise ValueError('Order cannot be cancelled')
        
        try:
            # Update order status
            order.status = OrderStatus.CANCELLED
            
            # Restore stock
            for item in order.items:
                item.product.add_stock(item.quantity)
            
            # Refund to wallet
            if order.payment_status == PaymentStatus.PAID:
                wallet = WalletService.get_wallet_by_user_id(customer_id)
                WalletService.refund(
                    wallet.id,
                    order.total_amount,
                    order.id,
                    f'Refund for cancelled order {order.order_number}'
                )
                order.payment_status = PaymentStatus.REFUNDED
            
            db.session.commit()
            return order
            
        except Exception as e:
            db.session.rollback()
            raise e
