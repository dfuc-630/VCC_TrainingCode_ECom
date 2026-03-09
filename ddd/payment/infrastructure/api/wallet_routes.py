"""
Wallet Management API Routes
Handles balance queries, deposits, withdrawals, and wallet activation
"""
from flask import Blueprint, request, jsonify
from ddd.payment.application.queries.wallet_queries import GetWalletBalanceQuery
from ddd.payment.application.commands import (
    DepositToWalletCommand,
    WithdrawFromWalletCommand,
    ActivateWalletCommand,
    DeactivateWalletCommand,
)
import logging

logger = logging.getLogger(__name__)


def create_wallet_routes(container):
    wallet_bp = Blueprint('wallet_api', __name__, url_prefix='/wallet')
    
    # ======================== GET /api/v1/wallet/<user_id>/balance ========================
    @wallet_bp.route('/<user_id>/balance', methods=['GET'])
    def get_wallet_balance(user_id):
        """Get wallet balance"""
        try:
            query = GetWalletBalanceQuery(user_id=user_id)
            handler = container.get('get_wallet_balance_handler')
            result = handler.execute(query)
            
            return jsonify(result), 200
        
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
                return jsonify({'error': 'Amount must be positive'}), 422
            
            # Create command
            command = DepositToWalletCommand(
                user_id=user_id,
                amount=amount,
                currency=data.get('currency', 'VND')
            )
            
            # Execute via handler
            handler = container.get('deposit_wallet_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Deposit successful',
                'data': result
            }), 200
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 422
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
                return jsonify({'error': 'Amount must be positive'}), 422
            
            # Create command
            command = WithdrawFromWalletCommand(
                user_id=user_id,
                amount=amount,
                currency=data.get('currency', 'VND')
            )
            
            # Execute via handler
            handler = container.get('withdraw_wallet_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Withdrawal successful',
                'data': result
            }), 200
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 422
        except Exception as e:
            logger.error(f"Error withdrawing from wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/activate ========================
    @wallet_bp.route('/<user_id>/activate', methods=['POST'])
    def activate_wallet(user_id):
        """Activate wallet"""
        try:
            # Create command
            command = ActivateWalletCommand(user_id=user_id)
            
            # Execute via handler
            handler = container.get('activate_wallet_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Wallet activated',
                'data': result
            }), 200
        
        except Exception as e:
            logger.error(f"Error activating wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/wallet/<user_id>/deactivate ========================
    @wallet_bp.route('/<user_id>/deactivate', methods=['POST'])
    def deactivate_wallet(user_id):
        """Deactivate wallet"""
        try:
            # Create command
            command = DeactivateWalletCommand(user_id=user_id)
            
            # Execute via handler
            handler = container.get('deactivate_wallet_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Wallet deactivated',
                'data': result
            }), 200
        
        except Exception as e:
            logger.error(f"Error deactivating wallet: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    return wallet_bp
