"""
Event handlers for payment domain
"""
from .wallet_event_handlers import CreateWalletOnUserCreatedHandler

__all__ = ['CreateWalletOnUserCreatedHandler']
