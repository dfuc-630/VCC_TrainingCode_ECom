"""
Product Catalog API Routes
Handles product creation, updates, and searches
"""
from flask import Blueprint, request, jsonify
import logging
from ddd.product_catalog.application.commands import (
    CreateProductCommand,
    UpdateProductCommand,
    ActivateProductCommand,
    DeactivateProductCommand,
)
from ddd.product_catalog.application.queries.product_queries import (
    GetProductQuery,
    GetSellerProductsQuery,
    SearchProductsQuery,
)

logger = logging.getLogger(__name__)


def create_product_routes(container):
    product_bp = Blueprint('product_api', __name__, url_prefix='/products')
    
    @product_bp.route('', methods=['POST'])
    def create_product():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            required = ['seller_id', 'name', 'description', 'price', 'quantity']
            missing = [f for f in required if f not in data]
            if missing:
                return jsonify({'error': 'Missing required fields', 'missing': missing}), 400
            
            if data['price'] <= 0:
                return jsonify({'error': 'Price must be positive'}), 422
            
            if data['quantity'] < 0:
                return jsonify({'error': 'Quantity must be non-negative'}), 422
            
            # Create command
            command = CreateProductCommand(
                seller_id=data['seller_id'],
                name=data['name'],
                description=data['description'],
                price=data['price'],
                quantity=data['quantity'],
                category_id=data.get('category_id'),
            )
            
            # Execute via handler
            handler = container.get('create_product_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Product created',
                'product': result
            }), 201
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 422
        except Exception as e:
            logger.error(f"Error creating product: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== GET /api/v1/products/<product_id> ========================
    @product_bp.route('/<product_id>', methods=['GET'])
    def get_product(product_id):
        """Get product details"""
        try:
            query = GetProductQuery(product_id=product_id)
            handler = container.get('get_product_handler')
            result = handler.execute(query)
            
            return jsonify(result), 200
        
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
            if not seller_id:
                return jsonify({'error': 'seller_id is required'}), 400
            
            # Create command
            command = UpdateProductCommand(
                product_id=product_id,
                seller_id=seller_id,
                name=data.get('name'),
                description=data.get('description'),
                price=data.get('price'),
                quantity=data.get('quantity'),
            )
            
            # Execute via handler
            handler = container.get('update_product_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Product updated',
                'product': result
            }), 200
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 422
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
            
            if not seller_id:
                return jsonify({'error': 'seller_id is required'}), 400
            
            # Create command
            command = ActivateProductCommand(
                product_id=product_id,
                seller_id=seller_id,
            )
            
            # Execute via handler
            handler = container.get('activate_product_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Product activated',
                'data': result
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
            
            if not seller_id:
                return jsonify({'error': 'seller_id is required'}), 400
            
            # Create command
            command = DeactivateProductCommand(
                product_id=product_id,
                seller_id=seller_id,
            )
            
            # Execute via handler
            handler = container.get('deactivate_product_handler')
            result = handler.execute(command)
            
            return jsonify({
                'message': 'Product deactivated',
                'data': result
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
            
            query = GetSellerProductsQuery(
                seller_id=seller_id,
                limit=limit,
                offset=offset,
                active_only=active_only,
            )
            
            handler = container.get('get_seller_products_handler')
            results = handler.execute(query)
            
            return jsonify(results), 200
        
        except Exception as e:
            logger.error(f"Error fetching seller products: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    # ======================== GET /api/v1/products/search ========================
    @product_bp.route('/search', methods=['GET'])
    def search_products():
        """Search products by keyword"""
        try:
            search_query = request.args.get('q', '')
            seller_id = request.args.get('seller_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            query = SearchProductsQuery(
                query=search_query,
                seller_id=seller_id,
                active_only=active_only,
                limit=limit,
                offset=offset,
            )
            
            handler = container.get('search_products_handler')
            results = handler.execute(query)
            
            return jsonify(results), 200
        
        except Exception as e:
            logger.error(f"Error searching products: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    return product_bp
