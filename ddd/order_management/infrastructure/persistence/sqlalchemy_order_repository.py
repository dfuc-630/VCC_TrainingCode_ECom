from typing import Optional, List
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
import logging

from ddd.order_management.infrastructure.persistence.sqlalchemy_order_model import OrderModel, OrderItemModel
from ddd.order_management.domain.repositories.order_repository_interface import OrderRepository
from ddd.order_management.domain.entities.order import Order
from ddd.order_management.domain.entities.order_item import OrderItem
from ddd.order_management.domain.value_objects.order import OrderStatus, OrderItemStatus, PaymentStatus, OrderId, OrderNumber
from ddd.shared.domain.value_objects.money import Money
from ddd.order_management.domain.exceptions import OrderNotFoundError

logger = logging.getLogger(__name__)


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository"""
    
    def __init__(self, session):
        self._session = session
    
    def save(self, order: Order) -> None:
        # Find existing model or create new one
        model = self._session.query(OrderModel).filter_by(id=order.id).first()
        
        if model is None:
            # New order
            model = OrderModel(id=order.id)
        
        # Map domain aggregate to ORM model
        model.order_number = order.order_number
        model.customer_id = order.customer_id
        model.seller_id = order.seller_id
        model.shipping_address = order.shipping_address
        model.shipping_phone = order.shipping_phone
        
        model.total_amount = Decimal(str(order.total_amount.amount))
        model.status = order.status.value
        model.payment_status = order.payment_status.value
        # model.error_message = order.error_message
        model.retry_count = order.retry_count
        
        # Save order items
        model.items = [self._item_to_model(item, order.id) for item in order.items]
        
        # Persist
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as e:
            self._session.rollback()
            raise
    
    def find_by_id(self, entity_id: str) -> Optional[Order]:
        model = self._session.query(OrderModel).filter_by(id=entity_id).first()
        logger.info(f"find_by_id: Queried for id={entity_id}, found={model is not None}")
        if model is None:
            logger.warning(f"find_by_id: No order model found for id={entity_id}")
            return None
        
        domain_order = self._to_domain(model)
        if domain_order is None:
            logger.warning(f"find_by_id: Failed to convert OrderModel to domain Order for id={entity_id}")
        return domain_order
    
    def find_by_order_number(self, order_number: OrderNumber) -> Optional[Order]:
        """Find order by order number"""
        model = self._session.query(OrderModel).filter_by(
            order_number=order_number.value
        ).first()
        return self._to_domain(model) if model else None
    
    def find_by_customer_id(self, customer_id: str, status: str = None) -> List[Order]:
        """Find all orders for a customer"""
        query = self._session.query(OrderModel).filter_by(customer_id=customer_id)
        
        if status:
            query = query.filter_by(status=status)
        
        models = query.all()
        return [self._to_domain(model) for model in models if model]
    
    def find_by_seller_id(self, seller_id: str, status: str = None) -> List[Order]:
        """Find all orders for a seller"""
        query = self._session.query(OrderModel).filter_by(seller_id=seller_id)
        
        if status:
            query = query.filter_by(status=status)
        
        models = query.all()
        return [self._to_domain(model) for model in models if model]
    
    def find_by_status(self, status: str) -> List[Order]:
        """Find all orders with specific status"""
        models = self._session.query(OrderModel).filter_by(status=status).all()
        return [self._to_domain(model) for model in models if model]
    
    def find_pending_orders(self) -> List[Order]:
        """Find all pending orders"""
        return self.find_by_status(OrderStatus.PENDING.value)
    
    def delete(self, entity_id: str) -> None:
        """Hard delete order"""
        model = self._session.query(OrderModel).filter_by(id=entity_id).first()
        if model:
            self._session.delete(model)
            self._session.commit()
    
    @staticmethod
    def _to_domain(model: OrderModel) -> Optional[Order]:
        if model is None:
            return None
        
        try:
            # Reconstruct value objects
            total = Money(amount=float(model.total_amount)) if model.total_amount else Money(0)
            
            # Reconstruct items first
            items = [SqlAlchemyOrderRepository._item_to_domain(item_model) for item_model in model.items]
            
            # Use factory method to reconstruct Order from persistence
            order = Order._from_persistence(
                order_id=model.id,
                order_number=model.order_number,
                customer_id=model.customer_id,
                seller_id=model.seller_id,
                shipping_address=model.shipping_address,
                shipping_phone=model.shipping_phone,
                status=model.status,
                payment_status=model.payment_status,
                total_amount=total,
                processing_at=None,  # Not tracked in OrderModel
                retry_count=model.retry_count,
                last_error=model.error_message,  # Maps to error_message in OrderModel
                sent_tele=False,  # Not tracked in OrderModel
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            
            # Set items directly
            order._items = items
            
            return order
        except Exception as e:
            logger.error(f"Error converting OrderModel to Order domain entity: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _item_to_model(item: OrderItem, order_id: str) -> OrderItemModel:
        """Convert OrderItem domain entity to ORM model"""
        return OrderItemModel(
            id=item.id,
            order_id=order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            price=Decimal(str(item.price.amount)),
            quantity=item.quantity,
            subtotal=Decimal(str(item.subtotal.amount)),
            status=item.status.value,
            processing_at=item.processing_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
    
    @staticmethod
    def _item_to_domain(model: OrderItemModel) -> OrderItem:
        """Convert OrderItem ORM model to domain entity"""
        return OrderItem._from_persistence(
            order_item_id=model.id,
            product_id=model.product_id,
            product_name=model.product_name,
            price=Money(amount=float(model.price)),
            quantity=model.quantity,
            status=model.status,
            processing_at=model.processing_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
