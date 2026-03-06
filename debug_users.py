#!/usr/bin/env python
"""Debug: Check if users are being saved to database"""
from integration.flask_app import create_ddd_app
from integration.db import db

app = create_ddd_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///ddd_test.db'})

with app.app_context():
    from ddd.user_management.infrastructure.persistence.sqlalchemy_user_model import UserModel
    users = db.session.query(UserModel).all()
    print(f"Total users in database: {len(users)}")
    for u in users:
        print(f"  - {u.id}: {u.email} (active: {u.is_active})")
