from ddd.shared.infrastructure.repository import Repository
from typing import Optional


class WalletRepository(Repository):
    """Repository interface for Wallet persistence"""
    
    def find_by_user_id(self, user_id: str) -> Optional:
        """Find wallet by user ID"""
        raise NotImplementedError
    
    def find_by_id(self, wallet_id: str) -> Optional:
        """Find wallet by ID"""
        raise NotImplementedError
