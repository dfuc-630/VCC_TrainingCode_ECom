"""
Wallet query handlers
"""
import logging

logger = logging.getLogger(__name__)


class GetWalletBalanceQueryHandler:
    """Handler for getting wallet balance"""
    
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository
    
    def execute(self, query):
        """
        Execute get balance query
        
        Args:
            query: GetWalletBalanceQuery
            
        Returns:
            dict with wallet info
            
        Raises:
            Exception: If wallet not found
        """
        logger.info(f"Fetching wallet balance for user: {query.user_id}")
        
        wallet = self.wallet_repository.find_by_user_id(query.user_id)
        if not wallet:
            raise Exception(f"Wallet not found for user {query.user_id}")
        
        return {
            'user_id': wallet.user_id,
            'balance': wallet.balance.amount,
            'currency': wallet.balance.currency,
            'is_active': wallet.is_active,
        }
