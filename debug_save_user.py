#!/usr/bin/env python
"""Debug: Test registration with direct function call"""
import sys
sys.path.insert(0, '/d:/PhucDD/flask/flask_project')

from integration.flask_app import create_ddd_app
from integration.db import db

app = create_ddd_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///ddd_test.db'})

print("Database file: sqlite:///ddd_test.db")
print("(This resolves to: d:\\PhucDD\\flask\\flask_project\\ddd_test.db)")

with app.app_context():
    from ddd.user_management.infrastructure.persistence.sqlalchemy_user_model import UserModel
    
    # Test: Create and save user directly
    from ddd.user_management.infrastructure.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
    from ddd.user_management.domain.entities.user import User
    from ddd.user_management.domain.value_objects.email import Email
    from ddd.user_management.domain.value_objects.password import Password
    from ddd.user_management.domain.value_objects.role import Role
    
    repo = SqlAlchemyUserRepository(db.session)
    
    # Create domain user
    user = User.register(
        email=Email("direct@test.com"),
        password="DirectPassword123",
        full_name="Direct Test",
        phone=None,
        role="customer"
    )
    
    print(f"\nCreated user with ID: {user.id}")
    
    # Save to database
    repo.save(user)
    print("Saved user to database")
    
    # Query it back
    found = repo.find_by_id(user.id)
    print(f"Found user after save: {found is not None}")
    if found:
        print(f"  Email: {found.email.value}")
    
    # Query all
    users = db.session.query(UserModel).all()
    print(f"\nTotal users in database: {len(users)}")
    for u in users:
        print(f"  - {u.id}: {u.email}")
