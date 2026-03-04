from typing import Optional
from decimal import Decimal

from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_model import WalletModel
from ddd.payment.domain.repositories.wallet_repository import WalletRepository
from ddd.payment.domain.entities.wallet import Wallet
from ddd.shared.domain.value_objects.money import Money


class SqlAlchemyWalletRepository(WalletRepository):
    """SQLAlchemy implementation of WalletRepository"""
    
    def __init__(self, session):
        self._session = session
    
    def save(self, wallet: Wallet) -> None:
        """Save wallet to database"""
        model = self._session.query(WalletModel).filter_by(id=wallet.id).first()
        
        if model is None:
            model = WalletModel(id=wallet.id)
        
        model.user_id = wallet.user_id
        model.balance = Decimal(str(wallet.balance.amount))
        model.is_active = wallet.is_active
        
        self._session.add(model)
        self._session.commit()
    
    def find_by_id(self, entity_id: str) -> Optional[Wallet]:
        """Find wallet by ID"""
        model = self._session.query(WalletModel).filter_by(id=entity_id).first()
        return self._to_domain(model) if model else None
    
    def find_by_user_id(self, user_id: str) -> Optional[Wallet]:
        """Find wallet by user ID"""
        model = self._session.query(WalletModel).filter_by(user_id=user_id).first()
        return self._to_domain(model) if model else None
    
    def delete(self, entity_id: str) -> None:
        """Delete wallet"""
        model = self._session.query(WalletModel).filter_by(id=entity_id).first()
        if model:
            self._session.delete(model)
            self._session.commit()
    
    @staticmethod
    def _to_domain(model: WalletModel) -> Optional[Wallet]:
        """Convert ORM model to domain entity"""
        if model is None:
            return None
        
        try:
            balance = Money(amount=float(model.balance))
            
            wallet = Wallet(
                wallet_id=model.id,
                user_id=model.user_id,
                balance=balance,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            
            return wallet
        except Exception:
            return None
