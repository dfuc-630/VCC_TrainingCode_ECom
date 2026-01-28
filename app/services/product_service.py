from app.models.product import Product
from app.extensions import db
from app.utils.helpers import slugify
from decimal import Decimal


class ProductService:
    """Product service handling product operations"""

    @staticmethod
    def create_product(seller_id: str, name: str, current_price: Decimal, **kwargs) -> Product:
        """Create new product"""
        slug = slugify(name)

        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        product = Product(
            seller_id=seller_id,
            name=name,
            slug=slug,
            current_price=current_price,
            description=kwargs.get("description"),
            detail=kwargs.get("detail"),
            category_id=kwargs.get("category_id"),
            original_price=kwargs.get("original_price"),
            stock_quantity=kwargs.get("stock_quantity", 0),
            image_url=kwargs.get("image_url"),
        )

        db.session.add(product)
        db.session.commit()

        return product

    @staticmethod
    def update_product(product_id: str, seller_id: str, **kwargs) -> Product:
        """Update product"""
        product = Product.query.filter_by(id=product_id, seller_id=seller_id).first()
        if not product or product.is_deleted:
            raise ValueError("Product not found")

        # Update slug if name changed
        if "name" in kwargs and kwargs["name"] != product.name:
            slug = slugify(kwargs["name"])
            base_slug = slug
            counter = 1
            while Product.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            kwargs["slug"] = slug

        product.update(**kwargs)
        return product

    @staticmethod
    def delete_product(product_id: str, seller_id: str):
        """Soft delete product"""
        product = Product.query.filter_by(id=product_id, seller_id=seller_id).first()
        if not product or product.is_deleted:
            raise ValueError("Product not found")

        product.soft_delete()
        return product

    @staticmethod
    def get_product_by_id(product_id: str) -> Product:
        """Get product by ID"""
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            raise ValueError("Product not found")
        return product

    @staticmethod
    def search_products(search: str = None, category_id: str = None,
    seller_id: str = None, is_active: bool = True, page: int = 1, per_page: int = 20,):
        """Search products with filters"""
        query = Product.query.filter_by(deleted_at=None)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        if search:
            query = query.filter(Product.name.contains(search))

        if category_id:
            query = query.filter_by(category_id=category_id)

        if seller_id:
            query = query.filter_by(seller_id=seller_id)

        return query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def deduct_stock(product_id: str, quantity: int) -> Product:
        """Deduct product stock with optimistic locking"""
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            raise ValueError("Product not found")

        product.deduct_stock(quantity)
        db.session.commit()

        return product
