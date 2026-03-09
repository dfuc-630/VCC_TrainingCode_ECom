from typing import Optional
from ddd.user_management.application.commands.register_user_command import RegisterUserCommand
from ddd.user_management.application.dto.user_dto import UserDTO, CreateUserResponseDTO
from ddd.user_management.domain.entities.user import User
from ddd.user_management.domain.value_objects.email import Email
from ddd.user_management.domain.value_objects.password import Password
from ddd.user_management.domain.value_objects.phone_number import PhoneNumber
from ddd.user_management.domain.value_objects.role import Role
from ddd.user_management.domain.exceptions import UserAlreadyExistsError
from ddd.user_management.application.commands.register_user_command import ChangePasswordCommand
from ddd.user_management.domain.exceptions import UserNotFoundError
import logging
logger = logging.getLogger(__name__)
class RegisterUserCommandHandler:
    """Handler for registering a new user"""
    
    def __init__(self, user_repository, event_dispatcher):
        
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command: RegisterUserCommand) -> CreateUserResponseDTO:
        # 1. Create value objects with validation
        email = Email(command.email)
        
        # 2. Check if email already exists
        if self.user_repository.email_exists(email):
            raise UserAlreadyExistsError(f"Email {email.value} is already registered")
        
        # 3. Create user aggregate root
        phone = PhoneNumber(command.phone) if command.phone else None
        role = Role(command.role)
        
        user = User.create(
            email=email,
            password_plain=command.password,
            role=role,
            full_name=command.full_name,
            phone=phone,
        )
        
        # 4. Save user to repository
        self.user_repository.save(user)
        
        # 5. Dispatch all domain events (UserCreatedEvent, etc.)
        # Payment domain will listen to UserCreatedEvent and create wallet
        for event in user.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        
        # 6. Clear uncommitted events after dispatch
        user.clear_uncommitted_events()
        
        return CreateUserResponseDTO(
            user_id=user.id,
            email=user.email.value,
        )


class ChangePasswordCommandHandler:
    """Handler for changing user password"""
    
    def __init__(self, user_repository, event_dispatcher):
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command):
        """Execute password change"""
        
        # Load user
        user = self.user_repository.find_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(f"User {command.user_id} not found")
        
        # Call domain method - validates old password, hashes new one
        user.change_password(command.old_password, command.new_password)
        
        # Save changes
        self.user_repository.save(user)
        
        # Dispatch events
        for event in user.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        user.clear_uncommitted_events()
        
        return UserDTO.from_entity(user)


class DeactivateUserCommandHandler:
    """Handler for deactivating user account"""
    
    def __init__(self, user_repository, event_dispatcher):
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command):
        """Execute user deactivation"""    
        user = self.user_repository.find_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(f"User {command.user_id} not found")
        
        user.deactivate()
        self.user_repository.save(user)
        
        for event in user.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        user.clear_uncommitted_events()
        
        return UserDTO.from_entity(user)


class UpdateUserProfileCommandHandler:
    """Handler for updating user profile"""
    
    def __init__(self, user_repository, event_dispatcher):
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command):
        """Execute profile update"""
        user = self.user_repository.find_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(f"User {command.user_id} not found")
        
        phone = PhoneNumber(command.phone) if command.phone else None
        user.update_profile(
            full_name=command.full_name,
            phone=phone,
        )
        
        self.user_repository.save(user)
        
        for event in user.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        user.clear_uncommitted_events()
        
        return UserDTO.from_entity(user)


class ActivateUserCommandHandler:
    """Handler for activating user account"""
    
    def __init__(self, user_repository, event_dispatcher):
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command):
        """Execute user activation"""
        user = self.user_repository.find_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(f"User {command.user_id} not found")
        
        user.activate()
        self.user_repository.save(user)
        
        for event in user.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        user.clear_uncommitted_events()
        
        return UserDTO.from_entity(user)
