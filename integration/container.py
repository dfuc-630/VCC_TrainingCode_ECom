"""
Service Container for Dependency Injection
Manages registration and retrieval of services, repositories, and handlers
"""

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
from app.services.kafka_producer_order_service import OrderKafkaProducer


class ServiceContainer:
    """
    Central service container for dependency injection
    
    Manages all repositories, handlers, and services
    Enables easy testing with fake implementations
    """
    
    def __init__(self, db_session=None, use_kafka: bool = False):
        """
        Initialize service container
        
        Args:
            db_session: SQLAlchemy database session
            use_kafka: Whether to use Kafka event dispatcher (True) or in-memory (False)
        """
        self._services = {}
        self._db_session = db_session
        self._use_kafka = use_kafka
        self._init_services()
    
    def _init_services(self):
        """Register all services, repositories, and handlers"""
        
        # ==== Event Dispatcher ====
        if self._use_kafka:
            kafka_producer = OrderKafkaProducer()
            event_dispatcher = KafkaEventDispatcher(kafka_producer=kafka_producer)
        else:
            event_dispatcher = InMemoryEventDispatcher()
        self._services['event_dispatcher'] = event_dispatcher
        
        # ==== Product Catalog ====
        product_repository = SqlAlchemyProductRepository(self._db_session)
        self._services['product_repository'] = product_repository
        
        # ==== Payment/Wallet ====
        wallet_repository = SqlAlchemyWalletRepository(self._db_session)
        self._services['wallet_repository'] = wallet_repository
        
        # ==== Inventory Service ====
        inventory_service = InventoryService(product_repository)
        self._services['inventory_service'] = inventory_service
        
        # ==== User Management ====
        # Repositories
        user_repository = SqlAlchemyUserRepository(self._db_session)
        self._services['user_repository'] = user_repository
        
        # Command Handlers
        self._services['register_user_handler'] = RegisterUserCommandHandler(
            user_repository,
            event_dispatcher,
        )
        self._services['change_password_handler'] = ChangePasswordCommandHandler(
            user_repository,
            event_dispatcher,
        )
        self._services['deactivate_user_handler'] = DeactivateUserCommandHandler(
            user_repository,
            event_dispatcher,
        )
        self._services['update_user_profile_handler'] = UpdateUserProfileCommandHandler(
            user_repository,
            event_dispatcher,
        )
        
        # Query Handlers
        self._services['get_user_by_email_handler'] = GetUserByEmailQueryHandler(user_repository)
        self._services['get_user_by_id_handler'] = GetUserByIdQueryHandler(user_repository)
        self._services['list_users_handler'] = ListUsersQueryHandler(user_repository)
        self._services['verify_user_password_handler'] = VerifyUserPasswordQueryHandler(user_repository)
        
        # ==== Order Management ====
        # Repositories
        order_repository = SqlAlchemyOrderRepository(self._db_session)
        self._services['order_repository'] = order_repository
        
        # Use Cases
        create_order_use_case = CreateOrderUseCase(
            order_repository=order_repository,
            product_repository=product_repository,
            wallet_repository=wallet_repository,
            inventory_service=inventory_service,
            event_dispatcher=event_dispatcher,
        )
        self._services['create_order_use_case'] = create_order_use_case
        
        # Command Handlers
        self._services['create_order_handler'] = CreateOrderCommandHandler(create_order_use_case)
        self._services['confirm_order_handler'] = ConfirmOrderCommandHandler(
            order_repository,
            event_dispatcher,
        )
        self._services['ship_order_handler'] = ShipOrderCommandHandler(
            order_repository,
            event_dispatcher,
        )
        self._services['complete_order_handler'] = CompleteOrderCommandHandler(
            order_repository,
            event_dispatcher,
        )
        self._services['cancel_order_handler'] = CancelOrderCommandHandler(
            order_repository,
            event_dispatcher,
        )
        
        # Query Handlers
        self._services['get_order_handler'] = GetOrderQueryHandler(order_repository)
        self._services['get_customer_orders_handler'] = GetCustomerOrdersQueryHandler(order_repository)
        self._services['get_seller_orders_handler'] = GetSellerOrdersQueryHandler(order_repository)
        self._services['list_pending_orders_handler'] = ListPendingOrdersQueryHandler(order_repository)
    
    def get(self, service_name: str):
        """
        Retrieve service by name
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The requested service
            
        Raises:
            KeyError: If service not found
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not found in container. Available: {list(self._services.keys())}")
        return self._services[service_name]
    
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
