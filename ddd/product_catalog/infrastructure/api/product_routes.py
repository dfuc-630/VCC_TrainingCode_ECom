"""
Product Catalog API Routes
Handles product creation, updates, and searches
"""
from flask import Blueprint, request, jsonify
import logging
from ddd.product_catalog.domain.exceptions import (
    ProductNotFoundError,
    InvalidProductError,
)

logger = logging.getLogger(__name__)


def create_product_routes(container):
    product_bp = Blueprint('product_api', __name__, url_prefix='/api/v1/products')
    
    # ======================== POST /api/v1/products ========================
    @product_bp.route('', methods=['POST'])
    def create_product():
        """Create new product"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            required = ['seller_id', 'name', 'description', 'price', 'quantity']
            missing = [f for f in required if f not in data]
            if missing:
                logger.warning(f"Missing fields: {missing}")
                return jsonify({'error': 'Missing required fields', 'missing': missing}), 400
            
            if data['price'] <= 0:
                return jsonify({'error': 'Price must be positive'}), 422
            
            if data['quantity'] < 0:
                return jsonify({'error': 'Quantity must be non-negative'}), 422
            
            logger.info(f"Creating product: {data['name']} (seller: {data['seller_id']})")
            
            from ddd.product_catalog.domain.entities.product import Product
            from ddd.shared.domain.value_objects import Money
            
            product = Product.create(
                seller_id=data['seller_id'],
                name=data['name'],
                description=data['description'],
                price=Money(amount=data['price'], currency='VND'),
                quantity=data['quantity']
            )
            
            product_repo = container.get('product_repository')
            product_repo.save(product)
            
            logger.info(f"✓ Product created: {product.id}")
            return jsonify({
                'message': 'Product created',
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price.amount,
                    'quantity': product.quantity,
                    'is_active': product.is_active
                }
            }), 201
        
        except InvalidProductError as e:
            return jsonify({'error': str(e)}), 422
        except Exception as e:
            logger.error(f"Error creating product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== GET /api/v1/products/<product_id> ========================
    @product_bp.route('/<product_id>', methods=['GET'])
    def get_product(product_id):
        """Get product details"""
        try:
            logger.info(f"Fetching product: {product_id}")
            
            product_repo = container.get('product_repository')
            product = product_repo.find_by_id(product_id)
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            return jsonify({
                'id': product.id,
                'seller_id': product.seller_id,
                'name': product.name,
                'description': product.description,
                'price': product.price.amount,
                'quantity': product.quantity,
                'is_active': product.is_active
            }), 200
        
        except ProductNotFoundError:
            return jsonify({'error': 'Product not found'}), 404
        except Exception as e:
            logger.error(f"Error fetching product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== PUT /api/v1/products/<product_id> ========================
    @product_bp.route('/<product_id>', methods=['PUT'])
    def update_product(product_id):
        """Update product (seller only)"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            seller_id = data.get('seller_id')
            
            logger.info(f"Updating product: {product_id}")
            
            product_repo = container.get('product_repository')
            product = product_repo.find_by_id(product_id)
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            if product.seller_id != seller_id:
                logger.warning(f"Unauthorized update: {seller_id}")
                return jsonify({'error': 'Unauthorized'}), 403
            
            if 'price' in data and data['price'] <= 0:
                return jsonify({'error': 'Price must be positive'}), 422
            
            if 'quantity' in data and data['quantity'] < 0:
                return jsonify({'error': 'Quantity must be non-negative'}), 422
            
            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'price' in data:
                from ddd.shared.domain.value_objects import Money
                product.price = Money(amount=data['price'], currency='VND')
            if 'quantity' in data:
                product.quantity = data['quantity']
            
            product_repo.save(product)
            
            logger.info(f"✓ Product updated: {product_id}")
            return jsonify({
                'message': 'Product updated',
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price.amount,
                    'quantity': product.quantity,
                    'is_active': product.is_active
                }
            }), 200
        
        except Exception as e:
            logger.error(f"Error updating product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/products/<product_id>/activate ========================
    @product_bp.route('/<product_id>/activate', methods=['POST'])
    def activate_product(product_id):
        """Activate product"""
        try:
            data = request.get_json() or {}
            seller_id = data.get('seller_id')
            
            logger.info(f"Activating product: {product_id}")
            
            product_repo = container.get('product_repository')
            product = product_repo.find_by_id(product_id)
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            if product.seller_id != seller_id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            if product.is_active:
                return jsonify({'message': 'Product already active'}), 200
            
            product.activate()
            product_repo.save(product)
            
            logger.info(f"✓ Product activated: {product_id}")
            return jsonify({
                'message': 'Product activated',
                'is_active': product.is_active
            }), 200
        
        except Exception as e:
            logger.error(f"Error activating product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== POST /api/v1/products/<product_id>/deactivate ========================
    @product_bp.route('/<product_id>/deactivate', methods=['POST'])
    def deactivate_product(product_id):
        """Deactivate product"""
        try:
            data = request.get_json() or {}
            seller_id = data.get('seller_id')
            
            logger.info(f"Deactivating product: {product_id}")
            
            product_repo = container.get('product_repository')
            product = product_repo.find_by_id(product_id)
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            if product.seller_id != seller_id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            if not product.is_active:
                return jsonify({'message': 'Product already inactive'}), 200
            
            product.deactivate()
            product_repo.save(product)
            
            logger.info(f"✓ Product deactivated: {product_id}")
            return jsonify({
                'message': 'Product deactivated',
                'is_active': product.is_active
            }), 200
        
        except Exception as e:
            logger.error(f"Error deactivating product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== GET /api/v1/products/seller/<seller_id> ========================
    @product_bp.route('/seller/<seller_id>', methods=['GET'])
    def get_seller_products(seller_id):
        """Get all products from seller"""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            
            logger.info(f"Fetching products for seller: {seller_id}")
            
            product_repo = container.get('product_repository')
            products = product_repo.find_by_seller_id(seller_id)
            
            if active_only:
                products = [p for p in products if p.is_active]
            
            products = products[offset:offset+limit]
            
            logger.info(f"✓ Fetched {len(products)} products")
            return jsonify([{
                'id': p.id,
                'name': p.name,
                'price': p.price.amount,
                'quantity': p.quantity,
                'is_active': p.is_active
            } for p in products]), 200
        
        except Exception as e:
            logger.error(f"Error fetching seller products: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== GET /api/v1/products/search ========================
    @product_bp.route('/search', methods=['GET'])
    def search_products():
        """Search products by keyword"""
        try:
            query = request.args.get('q', '')
            seller_id = request.args.get('seller_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            logger.info(f"Searching products: q='{query}'")
            
            product_repo = container.get('product_repository')
            all_products = product_repo.find_active(skip=0, limit=1000)
            
            if query:
                all_products = [
                    p for p in all_products 
                    if query.lower() in p.name.lower() or query.lower() in p.description.lower()
                ]
            
            if seller_id:
                all_products = [p for p in all_products if p.seller_id == seller_id]
            
            products = all_products[offset:offset+limit]
            
            logger.info(f"✓ Found {len(products)} products")
            return jsonify([{
                'id': p.id,
                'seller_id': p.seller_id,
                'name': p.name,
                'price': p.price.amount,
                'quantity': p.quantity,
                'is_active': p.is_active
            } for p in products]), 200
        
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    return product_bp
