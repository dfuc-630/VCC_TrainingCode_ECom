from typing import Optional, List
from ddd.user_management.application.queries.get_user_queries import (
    GetUserByEmailQuery,
    GetUserByIdQuery,
    ListUsersQuery,
    VerifyUserPasswordQuery,
)
from ddd.user_management.application.dto.user_dto import UserDTO
from ddd.user_management.domain.value_objects.email import Email


class GetUserByEmailQueryHandler:
    """Handler for retrieving user by email"""
    
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def execute(self, query: GetUserByEmailQuery) -> Optional[UserDTO]:
        """
        Execute query to find user by email
        
        Args:
            query: GetUserByEmailQuery with email
            
        Returns:
            UserDTO if found, None otherwise
        """
        email = Email(query.email)
        user = self.user_repository.find_by_email(email)
        
        if not user:
            return None
        
        return UserDTO.from_entity(user)


class GetUserByIdQueryHandler:
    """Handler for retrieving user by id"""
    
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def execute(self, query: GetUserByIdQuery) -> Optional[UserDTO]:
        """
        Execute query to find user by id
        
        Args:
            query: GetUserByIdQuery with user_id
            
        Returns:
            UserDTO if found, None otherwise
        """
        user = self.user_repository.find_by_id(query.user_id)
        
        if not user:
            return None
        
        return UserDTO.from_entity(user)


class ListUsersQueryHandler:
    """Handler for listing all users"""
    
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def execute(self, query: ListUsersQuery) -> List[UserDTO]:
        """
        Execute query to list users with pagination
        
        Args:
            query: ListUsersQuery with skip, limit, role filter
            
        Returns:
            List of UserDTO objects
        """
        users = self.user_repository.find_all(
            skip=query.skip,
            limit=query.limit,
            role=query.role,
        )
        
        return [UserDTO.from_entity(user) for user in users]


class VerifyUserPasswordQueryHandler:
    """Handler for verifying user password"""
    
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def execute(self, query: VerifyUserPasswordQuery) -> bool:
        """
        Execute query to verify user password
        
        Args:
            query: VerifyUserPasswordQuery with user_id and password
            
        Returns:
            True if password is correct, False otherwise
        """
        user = self.user_repository.find_by_id(query.user_id)
        
        if not user:
            return False
        
        return user.verify_password(query.password)
