from dataclasses import dataclass


@dataclass
class GetUserByEmailQuery:
    """Query to get user by email"""
    email: str


@dataclass
class GetUserByIdQuery:
    """Query to get user by id"""
    user_id: str


@dataclass
class ListUsersQuery:
    """Query to list all users"""
    skip: int = 0
    limit: int = 100
    role: str = None


@dataclass
class VerifyUserPasswordQuery:
    """Query to verify user password"""
    user_id: str
    password: str
