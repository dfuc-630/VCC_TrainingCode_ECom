"""
Wallet query classes
"""


class GetWalletBalanceQuery:
    """Query to get wallet balance"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
