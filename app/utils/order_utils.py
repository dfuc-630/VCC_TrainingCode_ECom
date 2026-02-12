from decimal import Decimal
from app.extensions import db
from app.models.product import Product
from app.enums import OrderItemStatus, OrderStatus, PaymentStatus
from app.models.order import Order, OrderItem
from app.utils.helpers import generate_order_number
from app.utils.kafka_utils import send_order_item_event
def _get_products_for_update(product_ids):
    products = (
        db.session.query(Product)
        .filter(Product.id.in_(product_ids))
        .all()
    )

    return {p.id: p for p in products}
def _validate_items(items_data, products_map):
    total_amount = Decimal("0")
    seller_id = None
    validated_items = []

    for item in items_data:
        product = products_map.get(item["product_id"])
        qty = item["quantity"]

        if not product:
            raise ValueError("Product not found")

        if qty <= 0:
            raise ValueError(f"Invalid quantity for {product.name}")

        if not product.is_active:
            raise ValueError(f"Product {product.name} is not available")

        if not product.has_stock(qty):
            raise ValueError(f"Insufficient stock for {product.name}")

        if seller_id is None:
            seller_id = product.seller_id
        elif seller_id != product.seller_id:
            raise ValueError("All products must be from the same seller")

        subtotal = product.current_price * qty
        total_amount += subtotal

        validated_items.append((product, qty, subtotal))

    return validated_items, seller_id, total_amount

def _create_order(customer_id, seller_id, total_amount, shipping_address, shipping_phone):
    order = Order(
        order_number=generate_order_number(),
        customer_id=customer_id,
        seller_id=seller_id,
        total_amount=total_amount,
        shipping_address=shipping_address,
        shipping_phone=shipping_phone,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.UNPAID,
    )

    db.session.add(order)
    db.session.flush()

    return order

def _create_order_items(order, validated_items):
    created_items = []
    for product, qty, subtotal in validated_items:
        product.stock_quantity -= qty

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.current_price,
            quantity=qty,
            subtotal=subtotal,
            status=OrderItemStatus.PENDING,
        )
        # send_order_item_event(order_item, order.id)
        db.session.add(order_item)
        created_items.append(order_item)

    return created_items