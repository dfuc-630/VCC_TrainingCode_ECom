#!/usr/bin/env python
"""
Debug script to test wallet creation
"""
import os
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://flask_user:Phuc06032004%40@localhost:5432/flask_db_new'

from integration.db import db
from integration.flask_app import create_app
from ddd.payment.domain.entities.wallet import Wallet
from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_repository import SqlAlchemyWalletRepository
from ddd.shared.domain.value_objects.money import Money
from uuid import uuid4

app = create_app()

with app.app_context():
    # Create test wallet
    user_id = str(uuid4())
    print(f"Creating wallet for user: {user_id}")
    
    wallet = Wallet.create(user_id=user_id, initial_balance=Money(amount=100000, currency='VND'))
    print(f"Wallet object created: {wallet}")
    print(f"  - wallet.id: {wallet.id}")
    print(f"  - wallet.user_id: {wallet.user_id}")
    print(f"  - wallet.balance.amount: {wallet.balance.amount}")
    
    repo = SqlAlchemyWalletRepository(db.session)
    print(f"\nSaving wallet...")
    try:
        repo.save(wallet)
        print(f"✅ Wallet saved successfully")
    except Exception as e:
        print(f"❌ Error saving wallet: {e}")
        import traceback
        traceback.print_exc()
    
    # Try to retrieve it
    print(f"\nRetrieving wallet...")
    retrieved = repo.find_by_user_id(user_id)
    if retrieved:
        print(f"✅ Wallet retrieved: {retrieved}")
        print(f"  - retrieved.user_id: {retrieved.user_id}")
        print(f"  - retrieved.balance.amount: {retrieved.balance.amount}")
    else:
        print(f"❌ Wallet not found")
