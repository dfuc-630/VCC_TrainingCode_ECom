"""
LoginUserCommandHandler
Handles user authentication
"""

from ddd.user_management.application.commands.login_user_command import LoginUserCommand, LoginUserResult
from ddd.user_management.domain.exceptions import UserNotFoundError, InvalidPasswordError
from ddd.user_management.domain.value_objects import Email

class LoginUserCommandHandler:
    def __init__(self, user_repository, event_dispatcher=None):
        self.user_repository = user_repository
        self.event_dispatcher = event_dispatcher

    def execute(self, command: LoginUserCommand):
        email_vo = Email(command.email)
        print(f"Attempting login for email: {email_vo}")
        user = self.user_repository.find_by_email(email_vo)
        if not user:
            raise UserNotFoundError('User not found')
        if not user.verify_password(command.password):
            raise InvalidPasswordError('Invalid password')
        return LoginUserResult(
            user_id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=str(user.role)
        )
