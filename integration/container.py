"""
Service Container for Dependency Injection
Manages registration and retrieval of services, repositories, and handlers
"""

import logging

from ddd.user_management.application.commands.handlers.login_user_handler import LoginUserCommandHandler

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
from ddd.payment.application.event_handlers import CreateWalletOnUserCreatedHandler
from ddd.payment.application.commands.handlers import (
    DepositToWalletCommandHandler,
    WithdrawFromWalletCommandHandler,
    ActivateWalletCommandHandler,
    DeactivateWalletCommandHandler,
)
from ddd.payment.application.queries.handlers import GetWalletBalanceQueryHandler
from ddd.product_catalog.application.commands.handlers import (
    CreateProductCommandHandler,
    UpdateProductCommandHandler,
    ActivateProductCommandHandler,
    DeactivateProductCommandHandler,
)
from ddd.product_catalog.application.queries.handlers import (
    GetProductQueryHandler,
    GetSellerProductsQueryHandler,
    SearchProductsQueryHandler,
)
from ddd.user_management.domain.events import UserCreatedEvent
from ddd.order_management.infrastructure.services.inventory_service import InventoryService
from app.services.kafka_producer_order_service import OrderKafkaProducer

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
        
        # ==== Event Dispatcher for general commands (InMemory) ====
        # Used for user, product, and other non-order domain events
        event_dispatcher = InMemoryEventDispatcher()
        self._services['event_dispatcher'] = event_dispatcher
        
        # ==== Event Dispatcher for orders (Kafka or InMemory based on config) ====
        # Used specifically for order creation/management
        if self._use_kafka:
            try:
                kafka_producer = OrderKafkaProducer()
                order_event_dispatcher = KafkaEventDispatcher(kafka_producer=kafka_producer)
            except ImportError:
                logger.warning("Kafka dependencies not available, using in-memory event dispatcher for orders")
                order_event_dispatcher = InMemoryEventDispatcher()
        else:
            order_event_dispatcher = InMemoryEventDispatcher()
        self._services['order_event_dispatcher'] = order_event_dispatcher
    
    def setup_event_handlers(self):
        """
        Setup event handlers subscriptions.
        Must be called after app has request context (in app context)
        """
        # Get the event dispatcher
        event_dispatcher = self._services['event_dispatcher']
        
        # Register event handlers
        # Payment domain listens to UserCreatedEvent from User domain and creates wallet
        wallet_repository = SqlAlchemyWalletRepository(self.session)
        wallet_handler = CreateWalletOnUserCreatedHandler(wallet_repository)
        event_dispatcher.subscribe(UserCreatedEvent, wallet_handler)
        logger.info("CreateWalletOnUserCreatedHandler registered")
    
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
            return self._services[service_name] # các service đã được khởi tạo sẵn
        
        # Create handler instances on-demand with fresh repositories
        event_dispatcher = self._services.get('event_dispatcher')
        
        # User handlers
        if service_name == 'register_user_handler':
            return RegisterUserCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        
        elif service_name == 'get_user_by_id_handler':
            return GetUserByIdQueryHandler(SqlAlchemyUserRepository(self.session))
        
        elif service_name == 'get_user_by_email_handler':
            return GetUserByEmailQueryHandler(SqlAlchemyUserRepository(self.session))
        
        elif service_name == 'change_password_handler':
            return ChangePasswordCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        
        elif service_name == 'deactivate_user_handler':
            return DeactivateUserCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        
        elif service_name == 'update_user_profile_handler':
            return UpdateUserProfileCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        
        elif service_name == 'list_users_handler':
            return ListUsersQueryHandler(SqlAlchemyUserRepository(self.session))
        
        elif service_name == 'login_user_handler':
            return LoginUserCommandHandler(SqlAlchemyUserRepository(self.session), event_dispatcher)
        
        # Order handlers
        elif service_name == 'get_order_handler':
            return GetOrderQueryHandler(SqlAlchemyOrderRepository(self.session))
        
        elif service_name == 'get_customer_orders_handler':
            return GetCustomerOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        
        elif service_name == 'get_seller_orders_handler':
            return GetSellerOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        
        elif service_name == 'list_pending_orders_handler':
            return ListPendingOrdersQueryHandler(SqlAlchemyOrderRepository(self.session))
        
        elif service_name == 'create_order_handler':
            
            order_repo = SqlAlchemyOrderRepository(self.session)
            product_repo = SqlAlchemyProductRepository(self.session)
            wallet_repo = SqlAlchemyWalletRepository(self.session)
            inventory_service = InventoryService(product_repo)
            order_event_dispatcher = self._services.get('order_event_dispatcher')
            use_case = CreateOrderUseCase(order_repo, product_repo, wallet_repo, inventory_service, order_event_dispatcher)
            
            return CreateOrderCommandHandler(use_case)
        
        elif service_name == 'confirm_order_handler':
            order_event_dispatcher = self._services.get('order_event_dispatcher')
            return ConfirmOrderCommandHandler(SqlAlchemyOrderRepository(self.session), order_event_dispatcher)
        
        elif service_name == 'ship_order_handler':
            order_event_dispatcher = self._services.get('order_event_dispatcher')
            return ShipOrderCommandHandler(SqlAlchemyOrderRepository(self.session), order_event_dispatcher)
        
        elif service_name == 'complete_order_handler':
            order_event_dispatcher = self._services.get('order_event_dispatcher')
            return CompleteOrderCommandHandler(SqlAlchemyOrderRepository(self.session), order_event_dispatcher)
        
        elif service_name == 'cancel_order_handler':
            order_event_dispatcher = self._services.get('order_event_dispatcher')
            return CancelOrderCommandHandler(SqlAlchemyOrderRepository(self.session), order_event_dispatcher)
        
        # Wallet handlers
        elif service_name == 'get_wallet_balance_handler':
            return GetWalletBalanceQueryHandler(SqlAlchemyWalletRepository(self.session))
        
        elif service_name == 'deposit_wallet_handler':
            return DepositToWalletCommandHandler(SqlAlchemyWalletRepository(self.session))
        
        elif service_name == 'withdraw_wallet_handler':
            return WithdrawFromWalletCommandHandler(SqlAlchemyWalletRepository(self.session))
        
        elif service_name == 'activate_wallet_handler':
            return ActivateWalletCommandHandler(SqlAlchemyWalletRepository(self.session))
        
        elif service_name == 'deactivate_wallet_handler':
            return DeactivateWalletCommandHandler(SqlAlchemyWalletRepository(self.session))
        
        # Product handlers
        elif service_name == 'create_product_handler':
            return CreateProductCommandHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'update_product_handler':
            return UpdateProductCommandHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'activate_product_handler':
            return ActivateProductCommandHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'deactivate_product_handler':
            return DeactivateProductCommandHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'get_product_handler':
            return GetProductQueryHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'get_seller_products_handler':
            return GetSellerProductsQueryHandler(SqlAlchemyProductRepository(self.session))
        
        elif service_name == 'search_products_handler':
            return SearchProductsQueryHandler(SqlAlchemyProductRepository(self.session))
        
        # Direct repository access
        elif service_name == 'wallet_repository':
            return SqlAlchemyWalletRepository(self.session)
        
        elif service_name == 'product_repository':
            return SqlAlchemyProductRepository(self.session)
        
        elif service_name == 'user_repository':
            return SqlAlchemyUserRepository(self.session)
        
        elif service_name == 'order_repository':
            return SqlAlchemyOrderRepository(self.session)
        
        raise KeyError(f"Service '{service_name}' not found in container")
    
    def register(self, name: str, instance): # for fake test
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
