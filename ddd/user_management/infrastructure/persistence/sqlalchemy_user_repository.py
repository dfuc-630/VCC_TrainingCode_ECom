from typing import Optional, List
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

from ddd.user_management.infrastructure.persistence.sqlalchemy_user_model import UserModel
from ddd.user_management.domain.repositories.user_repository_interface import UserRepository
from ddd.user_management.domain.entities.user import User
from ddd.user_management.domain.value_objects.email import Email
from ddd.user_management.domain.value_objects.password import Password
from ddd.user_management.domain.value_objects.phone_number import PhoneNumber
from ddd.user_management.domain.value_objects.role import Role
from ddd.user_management.domain.exceptions import UserAlreadyExistsError, UserNotFoundError


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository"""
    
    def __init__(self, session):
        """
        Args:
            session: SQLAlchemy database session
        """
        self._session = session
    
    def save(self, user: User) -> None:
        """
        Save user to database (insert or update)
        
        Converts domain User aggregate to ORM UserModel
        
        Args:
            user: User domain aggregate root
        """
        # Find existing model or create new one
        model = self._session.query(UserModel).filter_by(id=user.id).first()
        
        if model is None:
            # New user - create model
            model = UserModel(id=user.id)
        
        # Map domain entity to ORM model
        model.email = user.email.value
        model.password_hash = user._password.hashed_value  # Access internal password
        model.full_name = user.full_name
        model.phone = user.phone.value if user.phone else None
        model.role = user.role.value.value  # Get enum string value
        model.is_active = user.is_active
        model.deleted_at = user.deleted_at
        
        # Persist
        self._session.add(model)
        try:
            self._session.commit()
        except IntegrityError as e:
            self._session.rollback()
            if "unique constraint" in str(e):
                raise UserAlreadyExistsError(f"Email {user.email.value} already exists")
            raise
    
    def find_by_id(self, entity_id: str) -> Optional[User]:
        """
        Find user by ID
        
        Args:
            entity_id: User ID
            
        Returns:
            User domain entity if found, None otherwise
        """
        model = self._session.query(UserModel).filter_by(id=entity_id).first()
        return self._to_domain(model) if model else None
    
    def find_by_email(self, email: Email) -> Optional[User]:
        """
        Find user by email
        
        Args:
            email: Email value object
            
        Returns:
            User domain entity if found, None otherwise
        """
        model = self._session.query(UserModel).filter_by(email=email.value).first()
        return self._to_domain(model) if model else None
    
    def email_exists(self, email: Email) -> bool:
        """Check if email already exists"""
        return self._session.query(UserModel).filter_by(email=email.value).first() is not None
    
    def find_all(self, skip: int = 0, limit: int = 100, role: str = None) -> List[User]:
        """
        Find all users with pagination and optional role filter
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role: Optional role filter
            
        Returns:
            List of User domain entities
        """
        query = self._session.query(UserModel)
        
        if role:
            query = query.filter_by(role=role)
        
        models = query.offset(skip).limit(limit).all()
        return [self._to_domain(model) for model in models if model]
    
    def find_by_role(self, role: str) -> List[User]:
        """Find all users by role"""
        models = self._session.query(UserModel).filter_by(role=role).all()
        return [self._to_domain(model) for model in models if model]
    
    def delete(self, entity_id: str) -> None:
        """Perform hard delete"""
        model = self._session.query(UserModel).filter_by(id=entity_id).first()
        if model:
            self._session.delete(model)
            self._session.commit()
    
    @staticmethod
    def _to_domain(model: UserModel) -> Optional[User]:
        """
        Convert SQLAlchemy ORM model to domain User entity
        
        This is the key mapping between database representation and domain logic
        
        Args:
            model: UserModel ORM instance
            
        Returns:
            User domain entity with all value objects properly initialized
        """
        if model is None:
            return None
        
        try:
            # Reconstruct value objects from ORM data
            email = Email(model.email)
            password = Password(model.password_hash)  # Already hashed from DB
            role = Role(model.role)
            phone = PhoneNumber(model.phone) if model.phone else None
            
            # Create domain entity
            user = User(
                user_id=model.id,
                email=email,
                password=password,
                full_name=model.full_name,
                phone=phone,
                role=role,
            )
            
            # Set persistence-specific attributes
            user._is_active = model.is_active
            user._deleted_at = model.deleted_at
            user._created_at = model.created_at
            user._updated_at = model.updated_at
            
            return user
        except Exception as e:
            # Log the error for debugging
            logger.error(f"Failed to convert UserModel to User domain entity: {str(e)}", exc_info=True)
            return None
    def find_by_username(self, username):
        user = self._session.query(UserModel).filter_by(username=username).first()
        return user

    def username_exists(self, username):
        return self._session.query(UserModel).filter_by(username=username).first() is not None