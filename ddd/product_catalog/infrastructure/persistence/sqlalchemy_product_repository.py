from typing import Optional, List
from decimal import Decimal

from ddd.product_catalog.infrastructure.persistence.sqlalchemy_product_model import ProductModel
from ddd.product_catalog.domain.repositories.product_repository import ProductRepository
from ddd.product_catalog.domain.entities.product import Product
from ddd.shared.domain.value_objects.money import Money


class SqlAlchemyProductRepository(ProductRepository):
    """SQLAlchemy implementation of ProductRepository"""
    
    def __init__(self, session):
        self._session = session
    
    def save(self, product: Product) -> None:
        """Save product to database"""
        model = self._session.query(ProductModel).filter_by(id=product.id).first()
        
        if model is None:
            model = ProductModel(id=product.id)
        
        model.seller_id = product.seller_id
        model.name = product.name
        model.description = product.description
        model.price = Decimal(str(product.price.amount))
        model.quantity = product.quantity
        model.is_active = product.is_active
        
        self._session.add(model)
        self._session.commit()
    
    def find_by_id(self, entity_id: str) -> Optional[Product]:
        """Find product by ID"""
        model = self._session.query(ProductModel).filter_by(id=entity_id).first()
        return self._to_domain(model) if model else None
    
    def find_by_seller_id(self, seller_id: str) -> List[Product]:
        """Find all products for a seller"""
        models = self._session.query(ProductModel).filter_by(seller_id=seller_id).all()
        return [self._to_domain(model) for model in models if model]
    
    def find_active(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Find all active products"""
        models = self._session.query(ProductModel).filter_by(is_active=True).offset(skip).limit(limit).all()
        return [self._to_domain(model) for model in models if model]
    
    def find_by_name(self, name: str) -> Optional[Product]:
        """Find product by name"""
        model = self._session.query(ProductModel).filter_by(name=name).first()
        return self._to_domain(model) if model else None
    
    def delete(self, entity_id: str) -> None:
        """Delete product"""
        model = self._session.query(ProductModel).filter_by(id=entity_id).first()
        if model:
            self._session.delete(model)
            self._session.commit()
    
    @staticmethod
    def _to_domain(model: ProductModel) -> Optional[Product]:
        """Convert ORM model to domain entity"""
        if model is None:
            return None
        
        try:
            price = Money(amount=float(model.price))
            
            product = Product(
                product_id=model.id,
                seller_id=model.seller_id,
                name=model.name,
                description=model.description,
                price=price,
                quantity=model.quantity,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            
            return product
        except Exception:
            return None
