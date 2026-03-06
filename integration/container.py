"""
Service Container for Dependency Injection
Manages registration and retrieval of services, repositories, and handlers
"""

import logging

logger = logging.getLogger(__name__)

from ddd.shared.infrastructure.event_dispatcher import InMemoryEventDispatcher, KafkaEventDispatcher
from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from ddd.user_management.application.commands.handlers.register_user_handler import (
    RegisterUserCommandHandler,
    ChangePasswordCommandHandler,
    DeactivateUserCommandHandler,
    UpdateUserProfileCommandHandler,
)
from ddd.user_management.application.queries.handlers.get_user_handlers import (
    GetUserByEmailQueryHandler,
    GetUserByIdQueryHandler,
    ListUsersQueryHandler,
    VerifyUserPasswordQueryHandler,
)

from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
from ddd.order_management.application.commands.handlers.order_command_handlers import (
    ConfirmOrderCommandHandler,
    ShipOrderCommandHandler,
    CompleteOrderCommandHandler,
    CancelOrderCommandHandler,
)
from ddd.order_management.application.commands.handlers.create_order_handler import CreateOrderCommandHandler
from ddd.order_management.application.queries.handlers.get_order_handlers import (
    GetOrderQueryHandler,
    GetCustomerOrdersQueryHandler,
    GetSellerOrdersQueryHandler,
    ListPendingOrdersQueryHandler,
)
from ddd.order_management.application.use_cases.create_order_use_case import CreateOrderUseCase

from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
from ddd.order_management.infrastructure.services.inventory_service import InventoryService


class ServiceContainer:
    """
    Central service container for dependency injection
    
    Manages all repositories, handlers, and services
    Enables easy testing with fake implementations
    """
    
    def __init__(self, db=None, db_session=None, use_kafka: bool = False):
        """
        Initialize service container
        
        Args:
            db: SQLAlchemy instance (preferred - provides request-scoped session)
            db_session: Explicit database session (legacy, for testing)
            use_kafka: Whether to use Kafka event dispatcher (True) or in-memory (False)
        """
        self._services = {}
        self._db = db
        self._db_session = db_session
        self._use_kafka = use_kafka
        self._init_services()
    
    @property
    def session(self):
        """Get current request-scoped session"""
        if self._db:
            return self._db.session
        return self._db_session
    
    def _init_services(self):
        """Register all services - most will use current scoped session via get() method"""
        
        # ==== Event Dispatcher (doesn't depend on session) ====
        if self._use_kafka:
            try:
                from app.services.kafka_producer_order_service import OrderKafkaProducer
                kafka_producer = OrderKafkaProducer()
                event_dispatcher = KafkaEventDispatcher(kafka_producer=kafka_producer)
            except ImportError:
                logger.warning("Kafka dependencies not available, using in-memory event dispatcher")
                event_dispatcher = InMemoryEventDispatcher()
        else:
            event_dispatcher = InMemoryEventDispatcher()
        self._services['event_dispatcher'] = event_dispatcher
    
    def get(self, service_name: str):
        """
        Retrieve service by name
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The requested service
            
        Raises:
            KeyError: If service not found in services or known handlers
        """
        # Non-session-dependent services
        if service_name in self._services:
            return self._services[service_name]
        
        # Create handler instances on-demand with fresh repositories
        event_dispatcher = self._services.get('event_dispatcher')
        
        # User handlers
        if service_name == 'register_user_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return RegisterUserCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        elif service_name == 'get_user_by_id_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return GetUserByIdQueryHandler(SqlAlchemyUserRepository(self.session))
        elif service_name == 'get_user_by_email_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return GetUserByEmailQueryHandler(SqlAlchemyUserRepository(self.session))
        elif service_name == 'change_password_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return ChangePasswordCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        elif service_name == 'deactivate_user_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return DeactivateUserCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        elif service_name == 'list_users_handler':
            from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
            return ListUsersQueryHandler(SqlAlchemyUserRepository(self.session))
        
        # Order handlers
        elif service_name == 'get_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return GetOrderQueryHandler(SqlAlchemyOrderRepository(self.session))
        elif service_name == 'get_customer_orders_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return GetCustomerOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        elif service_name == 'get_seller_orders_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return GetSellerOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        elif service_name == 'list_pending_orders_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return ListPendingOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        elif service_name == 'create_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            order_repo = SqlAlchemyOrderRepository(self.session)
            product_repo = SqlAlchemyProductRepository(self.session)
            wallet_repo = SqlAlchemyWalletRepository(self.session)
            inventory_service = InventoryService(product_repo)
            use_case = CreateOrderUseCase(order_repo, product_repo, wallet_repo, inventory_service, event_dispatcher)
            return CreateOrderCommandHandler(use_case)
        elif service_name == 'confirm_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return ConfirmOrderCommandHandler(SqlAlchemyOrderRepository(self.session), event_dispatcher)
        elif service_name == 'ship_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return ShipOrderCommandHandler(SqlAlchemyOrderRepository(self.session), event_dispatcher)
        elif service_name == 'complete_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return CompleteOrderCommandHandler(SqlAlchemyOrderRepository(self.session), event_dispatcher)
        elif service_name == 'cancel_order_handler':
            from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
            return CancelOrderCommandHandler(SqlAlchemyOrderRepository(self.session), event_dispatcher)
        
        # Wallet handlers
        elif service_name == 'deposit_handler':
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            return DepositCommandHandler(SqlAlchemyWalletRepository(self.session), event_dispatcher)
        elif service_name == 'withdraw_handler':
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            return WithdrawCommandHandler(SqlAlchemyWalletRepository(self.session), event_dispatcher)
        elif service_name == 'get_wallet_balance_handler':
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            return GetWalletBalanceQueryHandler(SqlAlchemyWalletRepository(self.session))
        elif service_name == 'activate_wallet_handler':
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            return ActivateWalletCommandHandler(SqlAlchemyWalletRepository(self.session), event_dispatcher)
        elif service_name == 'deactivate_wallet_handler':
            from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
            return DeactivateWalletCommandHandler(SqlAlchemyWalletRepository(self.session), event_dispatcher)
        
        # Product handlers
        elif service_name == 'get_product_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return GetProductQueryHandler(SqlAlchemyProductRepository(self.session))
        elif service_name == 'get_seller_products_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return GetSellerProductsQueryHandler(SqlAlchemyProductRepository(self.session))
        elif service_name == 'search_products_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return SearchProductsQueryHandler(SqlAlchemyProductRepository(self.session))
        elif service_name == 'create_product_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return CreateProductCommandHandler(SqlAlchemyProductRepository(self.session), event_dispatcher)
        elif service_name == 'update_product_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return UpdateProductCommandHandler(SqlAlchemyProductRepository(self.session), event_dispatcher)
        elif service_name == 'activate_product_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return ActivateProductCommandHandler(SqlAlchemyProductRepository(self.session), event_dispatcher)
        elif service_name == 'deactivate_product_handler':
            from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_repository import SqlAlchemyProductRepository
            return DeactivateProductCommandHandler(SqlAlchemyProductRepository(self.session), event_dispatcher)
        
        raise KeyError(f"Service '{service_name}' not found in container")
    
    def register(self, name: str, instance):
        """
        Register a service in the container
        
        Args:
            name: Service name
            instance: Service instance
        """
        self._services[name] = instance
    
    def has(self, service_name: str) -> bool:
        """Check if service is registered"""
        return service_name in self._services
    
    def list_services(self):
        """List all registered services"""
        return list(self._services.keys())
