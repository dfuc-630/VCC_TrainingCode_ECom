import random
import string
from datetime import datetime
from slugify import slugify as python_slugify


def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'ORD{timestamp}{random_str}'


def slugify(text: str) -> str:
    """Generate URL-friendly slug"""
    return python_slugify(text)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions