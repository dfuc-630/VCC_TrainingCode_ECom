"""
Wallet command classes
"""


class DepositToWalletCommand:
    """Command to deposit funds to a wallet"""
    
    def __init__(self, user_id: str, amount: float, currency: str = 'VND'):
        self.user_id = user_id
        self.amount = amount
        self.currency = currency


class WithdrawFromWalletCommand:
    """Command to withdraw funds from a wallet"""
    
    def __init__(self, user_id: str, amount: float, currency: str = 'VND'):
        self.user_id = user_id
        self.amount = amount
        self.currency = currency


class ActivateWalletCommand:
    """Command to activate a wallet"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id


class DeactivateWalletCommand:
    """Command to deactivate a wallet"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
