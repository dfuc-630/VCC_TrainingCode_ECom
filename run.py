import os
from dotenv import load_dotenv
from app import create_app, db
from app.models.user import User

# Load environment variables
load_dotenv()

# Create app instance
app = create_app()


@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    print('Database initialized successfully!')


@app.cli.command()
def drop_db():
    """Drop all tables"""
    if input('Are you sure you want to drop all tables? (yes/no): ') == 'yes':
        db.drop_all()
        print('Database dropped successfully!')
    else:
        print('Operation cancelled')


@app.cli.command()
def create_admin():
    """Create admin user"""
    email = input('Admin email: ')
    username = input('Admin username: ')
    password = input('Admin password: ')
    
    if User.query.filter_by(email=email).first():
        print('Email already exists')
        return
    
    if User.query.filter_by(username=username).first():
        print('Username already exists')
        return
    
    admin = User(
        email=email,
        username=username,
        full_name='System Administrator',
        role='admin',
        is_active=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print('Admin user created successfully!')


if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'True') == 'True'
    )
