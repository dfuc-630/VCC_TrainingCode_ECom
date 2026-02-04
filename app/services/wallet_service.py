from app.models.wallet import Wallet, WalletTransaction
from app.extensions import db
from decimal import Decimal
from app.enums import TransactionType
from sqlalchemy.exc import SQLAlchemyError


class WalletService:
    @staticmethod
    def get_wallet_by_user_id(user_id: str) -> Wallet:
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Wallet not found")
        return wallet

    @staticmethod
    def deposit(wallet_id: str, amount: Decimal, description: str = None) -> tuple[Wallet, WalletTransaction]:
        try:
            wallet = (
                db.session.query(Wallet)
                .filter_by(id=wallet_id)
                .with_for_update()
                .first()
            ) # lock transaction

            if not wallet:
                raise ValueError("Wallet not found")

            balance_before = wallet.balance
            wallet.add_balance(amount)
            balance_after = wallet.balance

            transaction = WalletTransaction(
                wallet_id=wallet_id,
                type=TransactionType.DEPOSIT,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=description or "Deposit",
            )

            db.session.add(transaction)
            db.session.commit()

            return wallet, transaction

        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def deduct(wallet_id: str, amount: Decimal, order_id: str = None, description: str = None, commit: bool = True) -> WalletTransaction:
        if not order_id:
            raise ValueError("order_id is required for payment")

        existed = (
            db.session.query(WalletTransaction.id)
            .filter(
                WalletTransaction.order_id == order_id,
                WalletTransaction.type == TransactionType.PAYMENT
            )
            .first()
        )

        if existed:
            print(f"Payment already processed for order {order_id}")
            return None

        wallet = (
            db.session.query(Wallet)
            .filter_by(id=wallet_id)
            .with_for_update()
            .first()
        )
        if not wallet:
            raise ValueError("Wallet not found")
        if wallet.balance < amount:
            raise ValueError("Insufficient balance")

        balance_before = wallet.balance
        wallet.deduct_balance(amount)
        balance_after = wallet.balance

        transaction = WalletTransaction(
            wallet_id=wallet_id,
            order_id=order_id,
            type=TransactionType.PAYMENT,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or "Payment",
        )

        db.session.add(transaction)
        if commit is True:
            db.session.commit()

        return transaction

    @staticmethod
    def refund(wallet_id: str, amount: Decimal, order_id: str = None, description: str = None, commit: bool = True) -> WalletTransaction:
        wallet = (
            db.session.query(Wallet)
            .filter_by(id=wallet_id)
            .with_for_update()
            .first()
        )
        if not wallet:
            raise ValueError("Wallet not found")

        balance_before = wallet.balance
        wallet.add_balance(amount)
        balance_after = wallet.balance

        transaction = WalletTransaction(
            wallet_id=wallet_id,
            order_id=order_id,
            type=TransactionType.REFUND,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description or "Refund",
        )

        db.session.add(transaction)
        if commit is True:
            db.session.commit()

        return transaction

    @staticmethod
    def get_transactions(wallet_id: str, page: int = 1, per_page: int = 20):
        """Get wallet transactions with pagination"""
        return (
            WalletTransaction.query.filter_by(wallet_id=wallet_id)
            .order_by(WalletTransaction.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
