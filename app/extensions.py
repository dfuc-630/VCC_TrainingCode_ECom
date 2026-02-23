from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
import os
import redis

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()


# Redis client dùng cho stock / rate limiting / cache
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=False)
