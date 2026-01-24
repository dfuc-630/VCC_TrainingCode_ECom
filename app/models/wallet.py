from app.models.base import BaseModel
from app.extensions import db
from decimal import Decimal
from app.enums import TransactionType


class Wallet(BaseModel):
    """Wallet model"""

    __tablename__ = "wallets"

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    balance = db.Column(db.Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    transactions = db.relationship(
        "WalletTransaction",
        backref="wallet",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def can_deduct(self, amount: Decimal) -> bool:
        """Check if wallet has sufficient balance"""
        return self.balance >= amount

    def add_balance(self, amount: Decimal):
        """Add balance to wallet"""
        self.balance += amount
        return self

    def deduct_balance(self, amount: Decimal):
        """Deduct balance from wallet"""
        if not self.can_deduct(amount):
            raise ValueError("Insufficient balance")
        self.balance -= amount
        return self

    def to_dict(self):
        data = super().to_dict()
        data["balance"] = float(self.balance)
        return data


class WalletTransaction(BaseModel):
    """Wallet transaction model"""

    __tablename__ = "wallet_transactions"

    wallet_id = db.Column(
        db.String(36),
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id = db.Column(
        db.String(36),
        db.ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type = db.Column(db.Enum(TransactionType, name="transaction_types"), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    balance_before = db.Column(db.Numeric(15, 2), nullable=False)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        data = super().to_dict()
        data["amount"] = float(self.amount)
        data["balance_before"] = float(self.balance_before)
        data["balance_after"] = float(self.balance_after)
        return data
