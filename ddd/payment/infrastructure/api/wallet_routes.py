"""
Wallet Management API Routes
Handles balance queries, deposits, withdrawals, and wallet activation
"""
from flask import Blueprint, request, jsonify
import logging
from ddd.payment.domain.exceptions import (
    WalletNotFoundError,
    InsufficientBalanceError,
    WalletInactiveError,
)

logger = logging.getLogger(__name__)


def create_wallet_routes(container):
    wallet_bp = Blueprint('wallet_api', __name__, url_prefix='/api/v1/wallet')
    
    # ======================== GET /api/v1/wallet/<user_id>/balance ========================
    @wallet_bp.route('/<user_id>/balance', methods=['GET'])
    def get_wallet_balance(user_id):
        """Get wallet balance"""
        try:
            logger.info(f"Fetching wallet balance for user: {user_id}")
            
            wallet_repo = container.get('wallet_repository')
            wallet = wallet_repo.find_by_user_id(user_id)
            
            if not wallet:
                logger.warning(f"Wallet not found for user: {user_id}")
                return jsonify({'error': 'Wallet not found'}), 404
            
            return jsonify({
                'user_id': wallet.user_id,
                'balance': wallet.balance.amount,
                'currency': wallet.balance.currency,
                'is_active': wallet.is_active
            }), 200
        
        except Exception as e:
            logger.error(f"Error fetching wallet balance: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/deposit ========================
    @wallet_bp.route('/<user_id>/deposit', methods=['POST'])
    def deposit_wallet(user_id):
        """Deposit funds to wallet"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            amount = data.get('amount')
            if not amount or amount <= 0:
                logger.warning(f"Invalid amount for deposit: {amount}")
                return jsonify({'error': 'Amount must be positive'}), 422
            
            logger.info(f"Depositing {amount} to user: {user_id}")
            
            wallet_repo = container.get('wallet_repository')
            wallet = wallet_repo.find_by_user_id(user_id)
            
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404
            
            if not wallet.is_active:
                logger.warning(f"Wallet is inactive: {user_id}")
                return jsonify({'error': 'Wallet is inactive'}), 402
            
            from ddd.shared.domain.value_objects import Money
            deposit_amount = Money(amount=amount, currency=data.get('currency', 'VND'))
            
            if not wallet.deposit(deposit_amount):
                return jsonify({'error': 'Deposit failed'}), 500
            
            wallet_repo.save(wallet)
            
            logger.info(f"✓ Deposit successful: {amount} to user {user_id}")
            return jsonify({
                'message': 'Deposit successful',
                'new_balance': wallet.balance.amount
            }), 200
        
        except WalletInactiveError as e:
            return jsonify({'error': str(e)}), 402
        except Exception as e:
            logger.error(f"Error depositing to wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/withdraw ========================
    @wallet_bp.route('/<user_id>/withdraw', methods=['POST'])
    def withdraw_wallet(user_id):
        """Withdraw funds from wallet"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            amount = data.get('amount')
            if not amount or amount <= 0:
                logger.warning(f"Invalid amount for withdrawal: {amount}")
                return jsonify({'error': 'Amount must be positive'}), 422
            
            logger.info(f"Withdrawing {amount} from user: {user_id}")
            
            wallet_repo = container.get('wallet_repository')
            wallet = wallet_repo.find_by_user_id(user_id)
            
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404
            
            if not wallet.is_active:
                return jsonify({'error': 'Wallet is inactive'}), 403
            
            from ddd.shared.domain.value_objects import Money
            withdraw_amount = Money(amount=amount, currency=data.get('currency', 'VND'))
            
            if not wallet.has_sufficient_balance(withdraw_amount):
                logger.warning(f"Insufficient balance for user: {user_id}")
                return jsonify({'error': 'Insufficient balance'}), 402
            
            if not wallet.withdraw(withdraw_amount):
                return jsonify({'error': 'Withdrawal failed'}), 500
            
            wallet_repo.save(wallet)
            
            logger.info(f"✓ Withdrawal successful: {amount} from user {user_id}")
            return jsonify({
                'message': 'Withdrawal successful',
                'new_balance': wallet.balance.amount
            }), 200
        
        except InsufficientBalanceError as e:
            return jsonify({'error': str(e)}), 402
        except WalletInactiveError as e:
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            logger.error(f"Error withdrawing from wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/activate ========================
    @wallet_bp.route('/<user_id>/activate', methods=['POST'])
    def activate_wallet(user_id):
        """Activate wallet"""
        try:
            logger.info(f"Activating wallet for user: {user_id}")
            
            wallet_repo = container.get('wallet_repository')
            wallet = wallet_repo.find_by_user_id(user_id)
            
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404
            
            if wallet.is_active:
                return jsonify({'message': 'Wallet already active'}), 200
            
            wallet.activate()
            wallet_repo.save(wallet)
            
            logger.info(f"✓ Wallet activated for user: {user_id}")
            return jsonify({
                'message': 'Wallet activated',
                'is_active': wallet.is_active
            }), 200
        
        except Exception as e:
            logger.error(f"Error activating wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/deactivate ========================
    @wallet_bp.route('/<user_id>/deactivate', methods=['POST'])
    def deactivate_wallet(user_id):
        """Deactivate wallet"""
        try:
            logger.info(f"Deactivating wallet for user: {user_id}")
            
            wallet_repo = container.get('wallet_repository')
            wallet = wallet_repo.find_by_user_id(user_id)
            
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404
            
            if not wallet.is_active:
                return jsonify({'message': 'Wallet already inactive'}), 200
            
            wallet.deactivate()
            wallet_repo.save(wallet)
            
            logger.info(f"✓ Wallet deactivated for user: {user_id}")
            return jsonify({
                'message': 'Wallet deactivated',
                'is_active': wallet.is_active
            }), 200
        
        except Exception as e:
            logger.error(f"Error deactivating wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    return wallet_bp
