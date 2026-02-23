from typing import Dict, Iterable, Tuple

import redis

from app.extensions import db, redis_client
from app.models.product import Product
from app.models.order import OrderItem


# Lua script để reserve stock atomically cho nhiều product cùng lúc.
# KEYS:  danh sách key stock của product (stock:{product_id})
# ARGV:  danh sách quantity tương ứng
#
# Logic:
# 1. Kiểm tra tất cả key đều đủ stock (>= requested)
# 2. Nếu bất kỳ key nào không đủ → return {0, 'INSUFFICIENT_STOCK'}
# 3. Nếu đủ → DECRBY tất cả key và return {1, 'OK'}
RESERVE_STOCK_LUA = """
local n = #KEYS
for i = 1, n do
    local current = tonumber(redis.call('GET', KEYS[i]) or "-1")
    local requested = tonumber(ARGV[i])
    if current < 0 then
        return {0, 'MISSING_KEY'}
    end
    if current < requested then
        return {0, 'INSUFFICIENT_STOCK'}
    end
end

for i = 1, n do
    local requested = tonumber(ARGV[i])
    redis.call('DECRBY', KEYS[i], requested)
end

return {1, 'OK'}
"""


_reserve_stock_script = redis_client.register_script(RESERVE_STOCK_LUA)


def _stock_key(product_id: str) -> str:
    return f"stock:{product_id}"


def seed_stock_keys(products: Dict[str, Product]) -> None:
    """
    Đảm bảo mỗi product đã có key stock trong Redis (SETNX để không override).
    """
    if not products:
        return

    pipe = redis_client.pipeline()
    for product_id, product in products.items():
        key = _stock_key(product_id)
        pipe.setnx(key, int(product.stock_quantity))
    pipe.execute()


def reserve_stock_for_order_items(validated_items: Iterable[Tuple[Product, int, object]]) -> Tuple[bool, str]:
    """
    Reserve stock trên Redis cho toàn bộ items của 1 order (all-or-nothing).

    validated_items: iterable các tuple (product, quantity, subtotal)
    Returns: (success, message)
    """
    products: Dict[str, Product] = {}
    keys = []
    quantities = []

    for product, qty, _ in validated_items:
        product_id = str(product.id)
        products[product_id] = product
        keys.append(_stock_key(product_id))
        quantities.append(int(qty))

    # Seed stock từ DB sang Redis (chỉ lần đầu, dùng SETNX)
    seed_stock_keys(products)

    if not keys:
        return False, "No items to reserve"

    try:
        result = _reserve_stock_script(keys=keys, args=quantities)
        # result là list [success_flag, message]
        if not isinstance(result, (list, tuple)) or len(result) != 2:
            return False, "Invalid Redis script response"

        success_flag, message = result
        return bool(int(success_flag)), str(message)
    except redis.RedisError as e:
        return False, f"Redis error: {e}"


def rollback_redis_stock_for_order_items(order_items: Iterable[OrderItem]) -> None:
    """
    Rollback stock trên Redis cho toàn bộ items của 1 order (INCRBY).
    Dùng cho case order FAILED / CANCELLED toàn bộ.
    """
    items = list(order_items)
    if not items:
        return

    pipe = redis_client.pipeline()
    for item in items:
        key = _stock_key(str(item.product_id))
        pipe.incrby(key, int(item.quantity))
    pipe.execute()


def sync_redis_stock_to_db_for_order_items(order_items: Iterable[OrderItem]) -> None:
    """
    Đồng bộ stock từ Redis về DB cho các products xuất hiện trong order_items.
    Dùng cho case order SUCCESS: Redis là nguồn truth, DB chỉ mirror lại.
    """
    items = list(order_items)
    if not items:
        return

    product_ids = sorted({str(i.product_id) for i in items})
    if not product_ids:
        return

    # Lấy stock hiện tại từ Redis
    keys = [_stock_key(pid) for pid in product_ids]
    stocks = redis_client.mget(keys)

    # Map product_id -> redis_stock (int) nếu tồn tại
    redis_stock_map: Dict[str, int] = {}
    for pid, raw in zip(product_ids, stocks):
        if raw is not None:
            try:
                redis_stock_map[pid] = int(raw)
            except (TypeError, ValueError):
                continue

    if not redis_stock_map:
        return

    # Cập nhật DB theo Redis (với for_update để tránh race với các transaction khác)
    products = (
        db.session.query(Product)
        .filter(Product.id.in_(product_ids))
        .with_for_update()
        .all()
    )
    for product in products:
        pid = str(product.id)
        if pid in redis_stock_map:
            product.stock_quantity = redis_stock_map[pid]

