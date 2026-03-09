"""
Event handlers for wallet domain
Listens to events from other domains and creates wallets
"""
import logging
from ddd.user_management.domain.events import UserCreatedEvent
from ddd.payment.domain.entities.wallet import Wallet
from ddd.shared.domain.value_objects.money import Money

logger = logging.getLogger(__name__)


class CreateWalletOnUserCreatedHandler:
    """
    Event handler that creates a wallet when a user is created.
    
    This implements the DDD pattern where domains react to events from other domains.
    When UserManagement domain raises UserCreatedEvent, Payment domain reacts by creating wallet.
    """
    
    def __init__(self, wallet_repository):
        """
        Args:
            wallet_repository: Repository for persisting wallets
        """
        self.wallet_repository = wallet_repository
    
    def __call__(self, event: UserCreatedEvent) -> None:
        """
        Handle UserCreatedEvent by creating wallet for the user.
        
        Args:
            event: UserCreatedEvent containing user_id and other user info
        """
        try:
            logger.info(f"Creating wallet for user {event.user_id}")
            
            # Create wallet aggregate root
            wallet = Wallet.create(
                user_id=event.user_id,
                initial_balance=Money(amount=0, currency='VND')
            )
            
            # Persist wallet
            self.wallet_repository.save(wallet)
            logger.info(f"Wallet created successfully for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error creating wallet for user {event.user_id}: {e}", exc_info=True)
            # Don't raise - wallet creation failing shouldn't fail user registration
