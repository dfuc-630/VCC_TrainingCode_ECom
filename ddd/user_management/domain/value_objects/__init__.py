"""
User Management - Value Objects init
"""
from ddd.user_management.domain.value_objects.email import Email
from ddd.user_management.domain.value_objects.password import Password
from ddd.user_management.domain.value_objects.phone_number import PhoneNumber
from ddd.user_management.domain.value_objects.role import Role, UserRole

__all__ = ['Email', 'Password', 'PhoneNumber', 'Role', 'UserRole']
