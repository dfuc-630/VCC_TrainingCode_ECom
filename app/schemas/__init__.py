from .user_schema import UserSchema
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.enums import UserRole, OrderStatus, PaymentStatus


class UserRegisterSchema(Schema):
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    full_name = fields.Str(validate=validate.Length(max=255))
    phone = fields.Str(validate=validate.Length(max=20))
    role = fields.Str(
        required=True, validate=validate.OneOf([UserRole.CUSTOMER, UserRole.SELLER])
    )


class UserLoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class ProductCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str()
    detail = fields.Str()
    category_id = fields.Str()
    original_price = fields.Decimal(places=2)
    current_price = fields.Decimal(
        required=True, places=2, validate=validate.Range(min=0)
    )
    stock_quantity = fields.Int(validate=validate.Range(min=0))
    image_url = fields.Str(validate=validate.Length(max=500))


class ProductUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str()
    detail = fields.Str()
    category_id = fields.Str()
    original_price = fields.Decimal(places=2)
    current_price = fields.Decimal(places=2, validate=validate.Range(min=0))
    stock_quantity = fields.Int(validate=validate.Range(min=0))
    image_url = fields.Str(validate=validate.Length(max=500))
    is_active = fields.Bool()


class OrderItemSchema(Schema):
    product_id = fields.Str(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class OrderCreateSchema(Schema):
    items = fields.List(
        fields.Nested(OrderItemSchema), required=True, validate=validate.Length(min=1)
    )
    shipping_address = fields.Str(required=True)
    shipping_phone = fields.Str(required=True, validate=validate.Length(max=20))


class WalletDepositSchema(Schema):
    amount = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    description = fields.Str()
