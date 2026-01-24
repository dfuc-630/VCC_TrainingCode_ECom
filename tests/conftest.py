import pytest
from app import create_app, db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.product import Product
from app.models.category import Category
from decimal import Decimal


@pytest.fixture(scope='function')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


# User fixtures
@pytest.fixture
def customer_user(app):
    """Create a customer user"""
    user = User(
        email='customer@test.com',
        username='customer',
        full_name='Test Customer',
        phone='0901234567',
        role='customer',
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    
    # Create wallet for customer
    wallet = Wallet(user_id=user.id, balance=Decimal('1000000.00'))
    db.session.add(wallet)
    
    db.session.commit()
    return user


@pytest.fixture
def seller_user(app):
    """Create a seller user"""
    user = User(
        email='seller@test.com',
        username='seller',
        full_name='Test Seller',
        phone='0907654321',
        role='seller',
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Create an admin user"""
    user = User(
        email='admin@test.com',
        username='admin',
        full_name='Test Admin',
        role='admin',
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


# Auth token fixtures
@pytest.fixture
def customer_token(client, customer_user):
    """Get customer authentication token"""
    response = client.post('/api/auth/login', json={
        'username': 'customer',
        'password': 'password123'
    })
    return response.json['access_token']


@pytest.fixture
def seller_token(client, seller_user):
    """Get seller authentication token"""
    response = client.post('/api/auth/login', json={
        'username': 'seller',
        'password': 'password123'
    })
    return response.json['access_token']


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin authentication token"""
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'password123'
    })
    return response.json['access_token']


@pytest.fixture
def customer_headers(customer_token):
    """Customer authentication headers"""
    return {'Authorization': f'Bearer {customer_token}'}


@pytest.fixture
def seller_headers(seller_token):
    """Seller authentication headers"""
    return {'Authorization': f'Bearer {seller_token}'}


@pytest.fixture
def admin_headers(admin_token):
    """Admin authentication headers"""
    return {'Authorization': f'Bearer {admin_token}'}


# Data fixtures
@pytest.fixture
def category(app):
    """Create a test category"""
    category = Category(
        name='Electronics',
        slug='electronics',
        description='Electronic devices'
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def product(app, seller_user, category):
    """Create a test product"""
    product = Product(
        seller_id=seller_user.id,
        category_id=category.id,
        name='iPhone 15 Pro Max',
        slug='iphone-15-pro-max',
        description='Latest iPhone',
        detail='Detailed description',
        original_price=Decimal('35000000.00'),
        current_price=Decimal('29990000.00'),
        stock_quantity=10,
        image_url='https://example.com/iphone.jpg',
        is_active=True
    )
    db.session.add(product)
    db.session.commit()
    return product
