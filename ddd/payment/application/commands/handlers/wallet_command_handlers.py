"""
Wallet command handlers
Implements business logic for wallet operations
"""
import logging
from ddd.shared.domain.value_objects.money import Money

logger = logging.getLogger(__name__)


class DepositToWalletCommandHandler:
    """Handler for depositing funds to wallet"""
    
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository
    
    def execute(self, command):
        """
        Execute deposit command
        
        Args:
            command: DepositToWalletCommand
            
        Returns:
            dict with operation result
            
        Raises:
            WalletNotFoundError: If wallet not found
            WalletInactiveError: If wallet is inactive
        """
        logger.info(f"Executing deposit: user={command.user_id}, amount={command.amount}")
        
        # Validate amount
        if command.amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Find wallet
        wallet = self.wallet_repository.find_by_user_id(command.user_id)
        if not wallet:
            raise Exception(f"Wallet not found for user {command.user_id}")
        
        # Check if wallet is active
        if not wallet.is_active:
            raise Exception(f"Wallet is inactive for user {command.user_id}")
        
        # Execute deposit
        deposit_amount = Money(amount=command.amount, currency=command.currency)
        if not wallet.deposit(deposit_amount):
            raise Exception("Deposit operation failed")
        
        # Persist changes
        self.wallet_repository.save(wallet)
        
        logger.info(f"Deposit successful: user={command.user_id}, new_balance={wallet.balance.amount}")
        
        return {
            'user_id': wallet.user_id,
            'new_balance': wallet.balance.amount,
            'currency': wallet.balance.currency,
        }


class WithdrawFromWalletCommandHandler:
    """Handler for withdrawing funds from wallet"""
    
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository
    
    def execute(self, command):
        """
        Execute withdraw command
        
        Args:
            command: WithdrawFromWalletCommand
            
        Returns:
            dict with operation result
            
        Raises:
            WalletNotFoundError: If wallet not found
            WalletInactiveError: If wallet is inactive
            InsufficientBalanceError: If insufficient balance
        """
        logger.info(f"Executing withdrawal: user={command.user_id}, amount={command.amount}")
        
        # Validate amount
        if command.amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Find wallet
        wallet = self.wallet_repository.find_by_user_id(command.user_id)
        if not wallet:
            raise Exception(f"Wallet not found for user {command.user_id}")
        
        # Check if wallet is active
        if not wallet.is_active:
            raise Exception(f"Wallet is inactive for user {command.user_id}")
        
        # Check balance
        withdraw_amount = Money(amount=command.amount, currency=command.currency)
        if not wallet.has_sufficient_balance(withdraw_amount):
            raise Exception(f"Insufficient balance. Available: {wallet.balance.amount}, Requested: {command.amount}")
        
        # Execute withdrawal
        if not wallet.withdraw(withdraw_amount):
            raise Exception("Withdrawal operation failed")
        
        # Persist changes
        self.wallet_repository.save(wallet)
        
        logger.info(f"Withdrawal successful: user={command.user_id}, new_balance={wallet.balance.amount}")
        
        return {
            'user_id': wallet.user_id,
            'new_balance': wallet.balance.amount,
            'currency': wallet.balance.currency,
        }


class ActivateWalletCommandHandler:
    """Handler for activating wallet"""
    
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository
    
    def execute(self, command):
        """
        Execute wallet activation command
        
        Args:
            command: ActivateWalletCommand
            
        Returns:
            dict with operation result
        """
        logger.info(f"Executing wallet activation: user={command.user_id}")
        
        # Find wallet
        wallet = self.wallet_repository.find_by_user_id(command.user_id)
        if not wallet:
            raise Exception(f"Wallet not found for user {command.user_id}")
        
        # Activate if not already active
        if not wallet.is_active:
            wallet.activate()
            self.wallet_repository.save(wallet)
            logger.info(f"Wallet activated: user={command.user_id}")
        
        return {
            'user_id': wallet.user_id,
            'is_active': wallet.is_active,
        }


class DeactivateWalletCommandHandler:
    """Handler for deactivating wallet"""
    
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository
    
    def execute(self, command):
        """
        Execute wallet deactivation command
        
        Args:
            command: DeactivateWalletCommand
            
        Returns:
            dict with operation result
        """
        logger.info(f"Executing wallet deactivation: user={command.user_id}")
        
        # Find wallet
        wallet = self.wallet_repository.find_by_user_id(command.user_id)
        if not wallet:
            raise Exception(f"Wallet not found for user {command.user_id}")
        
        # Deactivate if not already inactive
        if wallet.is_active:
            wallet.deactivate()
            self.wallet_repository.save(wallet)
            logger.info(f"Wallet deactivated: user={command.user_id}")
        
        return {
            'user_id': wallet.user_id,
            'is_active': wallet.is_active,
        }
