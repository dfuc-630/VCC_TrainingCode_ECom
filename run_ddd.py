"""
DDD Application Entry Point
Runs the Flask app with DDD architecture
"""
import os
from dotenv import load_dotenv
from integration.flask_app import create_ddd_app

# Load environment variables
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s : %(message)s',
    force=True
)

logging.getLogger('werkzeug').setLevel(logging.INFO)

def create_config():
    """Create app configuration"""
    return {
        'SQLALCHEMY_DATABASE_URI': os.getenv(
            'DATABASE_URL', 
            'sqlite:///ddd_test.db'
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET', 'your-secret-key'),
        'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key'),
        'USE_KAFKA': os.getenv('USE_KAFKA', 'False').lower() == 'true',
        'TESTING': False,
        'DEBUG': os.getenv('DEBUG', 'True').lower() == 'true',
    }


if __name__ == '__main__':
    config = create_config()
    app = create_ddd_app(config)
    
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = config['DEBUG']
    
    print(f" Starting DDD Flask App")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   Database: {config['SQLALCHEMY_DATABASE_URI']}")
    print(f"   Kafka: {'Enabled' if config['USE_KAFKA'] else 'Disabled (In-Memory)'}")
    print()

    app.run(
        host=host,
        port=5001,
        debug=debug,
        use_reloader=False
    )
