#!/usr/bin/env python
"""Test user registration and retrieval in same context"""
from integration.flask_app import create_ddd_app
from integration.container import ServiceContainer
from integration.db import db

app = create_ddd_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///test_context.db'})

with app.app_context():
    from ddd.user_management.application.commands.register_user_command import RegisterUserCommand
    from ddd.user_management.application.queries.get_user_queries import GetUserByIdQuery
    
    # Create a container (like in the request)
    container = ServiceContainer(db=db, use_kafka=False)
    
    # Test 1: Register user
    print("Test 1: Register user")
    register_handler = container.get('register_user_handler')
    cmd = RegisterUserCommand(
        email=f"test{int(__import__('time').time())}@same-context.com",
        password="TestPassword123",
        full_name="Test User",
        phone=None,
        role="customer"
    )
    result = register_handler.execute(cmd)
    user_id = result.user_id
    print(f"  Registered user ID: {user_id}")
    
    # Test 2: Get user immediately after in same session
    print("\nTest 2: Get user by ID (same context)")
    get_handler = container.get('get_user_by_id_handler')
    query = GetUserByIdQuery(user_id=user_id)
    user_data = get_handler.execute(query)
    
    if user_data:
        print(f"  ✓ Found user: {user_data.email}")
    else:
        print(f"  ✗ User not found!")
        
        # Debug: Check database directly
        from ddd.user_management.infrastructure.persistence.sqlalchemy_user_model import UserModel
        db_users = db.session.query(UserModel).all()
        print(f"\n  Database has {len(db_users)} users:")
        for u in db_users:
            print(f"    - {u.id}: {u.email}")
