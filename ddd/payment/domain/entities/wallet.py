from uuid import uuid4
from datetime import datetime, timezone
from ddd.shared.domain.base_entity import AggregateRoot
from ddd.shared.domain.value_objects.money import Money


class Wallet(AggregateRoot):
    """Wallet aggregate root - represents user's payment balance"""
    
    def __init__(
        self,
        wallet_id: str,
        user_id: str,
        balance: Money,
        is_active: bool = True,
        created_at: datetime = None,
        updated_at: datetime = None,
    ):
        super().__init__(wallet_id)

        self.user_id = user_id
        self.balance = balance
        self.is_active = is_active

        if created_at:
            self._created_at = created_at
        if updated_at:
            self._updated_at = updated_at
    
    @staticmethod
    def create(user_id: str, initial_balance: Money = None) -> 'Wallet':
        """Create new wallet"""
        balance = initial_balance or Money(amount=0)
        wallet = Wallet(
            wallet_id=str(uuid4()),
            user_id=user_id,
            balance=balance,
        )
        return wallet
    
    def deposit(self, amount: Money) -> bool:
        """Deposit money to wallet"""
        if amount.amount <= 0:
            return False
        self.balance = self.balance.add(amount)
        self._updated_at = datetime.now(timezone.utc)
        return True
    
    def withdraw(self, amount: Money) -> bool:
        """Withdraw money from wallet"""
        if self.balance.amount < amount.amount:
            return False
        self.balance = self.balance.subtract(amount)
        self._updated_at = datetime.now(timezone.utc)
        return True
    
    def has_sufficient_balance(self, amount: Money) -> bool:
        """Check if wallet has sufficient balance"""
        return self.balance.amount >= amount.amount
    
    def activate(self):
        """Activate wallet for transactions"""
        self.is_active = True
        self._updated_at = datetime.now(timezone.utc)
    
    def deactivate(self):
        """Deactivate wallet"""
        self.is_active = False
        self._updated_at = datetime.now(timezone.utc)
