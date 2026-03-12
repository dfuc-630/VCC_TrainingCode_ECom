"""
Order Management API Routes
Fully integrated with async Kafka workers and Redis stock management
"""
from flask import Blueprint, request, jsonify
import logging
from ddd.order_management.application.queries.get_order_query import GetOrderQuery
from ddd.order_management.domain.exceptions import (
    OrderNotFoundError,
    InsufficientStockError,
    InsufficientBalanceError,
)
from ddd.order_management.application.commands import (
    CreateOrderCommand,
    CreateOrderItemCommand,
)

logger = logging.getLogger(__name__)


def create_order_routes(container):
    order_bp = Blueprint('order_api', __name__, url_prefix='/orders')
    
    @order_bp.route('', methods=['POST'])
    def create_order():
        try:
            data = request.get_json()
            if not data:
                logger.warning("Empty request body")
                return jsonify({'error': 'Request body is required'}), 400
            
            # Validate required fields
            required = ['customer_id', 'seller_id', 'items', 'shipping_address', 'shipping_phone']
            missing = [f for f in required if f not in data]
            if missing:
                logger.warning(f"Missing fields: {missing}")
                return jsonify({'error': 'Missing required fields', 'missing': missing}), 400
            
            # Validate items
            if not isinstance(data.get('items'), list) or len(data['items']) == 0:
                logger.warning("Invalid items")
                return jsonify({'error': 'Items must be non-empty list'}), 422
            
            for idx, item in enumerate(data['items']):
                if not item.get('product_id') or not isinstance(item.get('quantity'), int) or item['quantity'] <= 0:
                    logger.warning(f"Invalid item {idx}")
                    return jsonify({'error': f'Invalid item {idx}'}), 422
            
            logger.info(f"Creating order: customer={data['customer_id']}, items={len(data['items'])}")
            
            # Convert dict to command object
            items = [
                CreateOrderItemCommand(
                    product_id=item['product_id'],
                    quantity=item['quantity']
                )
                for item in data['items']
            ]
            
            command = CreateOrderCommand(
                customer_id=data['customer_id'],
                seller_id=data['seller_id'],
                items=items,
                shipping_address=data['shipping_address'],
                shipping_phone=data['shipping_phone']
            )
            
            # Execute via handler
            handler = container.get('create_order_handler')
            try:
                order_dto = handler.execute(command)
            except Exception as e:
                logger.error(f"Error executing create order command: {e}", exc_info=True)
                raise
            logger.info(f" Order created: {order_dto.order_id} (PENDING)")
            
            
            return jsonify({
                'message': 'Order created successfully',
                'order': order_dto.to_dict() if hasattr(order_dto, 'to_dict') else order_dto,
                'note': 'Processing asynchronously...'
            }), 201
        
        except InsufficientStockError as e:
            logger.warning(f"Stock error: {e}")
            return jsonify({'error': 'Insufficient stock', 'message': str(e)}), 409
        
        except InsufficientBalanceError as e:
            logger.warning(f"Balance error: {e}")
            return jsonify({'error': 'Insufficient balance', 'message': str(e)}), 402
        
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': 'Validation error', 'message': str(e)}), 422
        
        except Exception as e:
            logger.error(f"Error creating order: {e}", exc_info=True)
            return jsonify({'error': 'Server error', 'message': str(e)}), 500
    
    
    @order_bp.route('/<order_id>', methods=['GET'])
    def get_order(order_id):
        """Get order details"""
        try:
            logger.info(f"Fetching order: {order_id}")
            handler = container.get('get_order_handler')
            query = GetOrderQuery(order_id=order_id)
            order_dto = handler.execute(query)
            
            if not order_dto:
                return jsonify({'error': 'Order not found'}), 404
            
            return jsonify(
                order_dto.to_dict() if hasattr(order_dto, 'to_dict') else order_dto
            ), 200
        
        except OrderNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            logger.error(f"Error fetching order: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/<order_id>/confirm', methods=['POST'])
    def confirm_order(order_id):
        """Manually confirm order (admin only)"""
        try:
            logger.info(f"Confirming order: {order_id}")
            handler = container.get('confirm_order_handler')
            result = handler.execute({'order_id': order_id})
            
            return jsonify(result.to_dict() if hasattr(result, 'to_dict') else result), 200
        
        except OrderNotFoundError:
            return jsonify({'error': 'Order not found'}), 404
        except Exception as e:
            logger.error(f"Error confirming order: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/<order_id>/ship', methods=['POST'])
    def ship_order(order_id):
        """Update order status to SHIPPED"""
        try:
            data = request.get_json() or {}
            logger.info(f"Shipping order: {order_id}")
            
            handler = container.get('ship_order_handler')
            result = handler.execute({
                'order_id': order_id,
                'seller_id': data.get('seller_id'),
                'tracking_number': data.get('tracking_number')
            })
            
            return jsonify(result.to_dict() if hasattr(result, 'to_dict') else result), 200
        
        except OrderNotFoundError:
            return jsonify({'error': 'Order not found'}), 404
        except Exception as e:
            logger.error(f"Error shipping order: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/<order_id>/complete', methods=['POST'])
    def complete_order(order_id):
        """Update order status to COMPLETED"""
        try:
            logger.info(f"Completing order: {order_id}")
            handler = container.get('complete_order_handler')
            result = handler.execute({'order_id': order_id})
            
            return jsonify(result.to_dict() if hasattr(result, 'to_dict') else result), 200
        
        except OrderNotFoundError:
            return jsonify({'error': 'Order not found'}), 404
        except Exception as e:
            logger.error(f"Error completing order: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/<order_id>/cancel', methods=['POST'])
    def cancel_order(order_id):
        """Cancel order (only PENDING orders can be cancelled)"""
        try:
            data = request.get_json() or {}
            logger.info(f"Cancelling order: {order_id}")
            
            handler = container.get('cancel_order_handler')
            result = handler.execute({
                'order_id': order_id,
                'customer_id': data.get('customer_id'),
                'reason': data.get('reason')
            })
            
            return jsonify(result.to_dict() if hasattr(result, 'to_dict') else result), 200
        
        except OrderNotFoundError:
            return jsonify({'error': 'Order not found'}), 404
        except Exception as e:
            logger.error(f"Error cancelling order: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/customer/<customer_id>', methods=['GET'])
    def get_customer_orders(customer_id):
        """Get all orders for a customer"""
        try:
            status = request.args.get('status')
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            logger.info(f"Fetching orders for customer: {customer_id}")
            
            handler = container.get('get_customer_orders_handler')
            orders_dto = handler.execute({
                'customer_id': customer_id,
                'status': status,
                'limit': limit,
                'offset': offset
            })
            
            return jsonify([
                order.to_dict() if hasattr(order, 'to_dict') else order
                for order in orders_dto
            ]), 200
        
        except Exception as e:
            logger.error(f"Error fetching customer orders: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/seller/<seller_id>', methods=['GET'])
    def get_seller_orders(seller_id):
        """Get all orders for a seller"""
        try:
            status = request.args.get('status')
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            logger.info(f"Fetching orders for seller: {seller_id}")
            
            handler = container.get('get_seller_orders_handler')
            orders_dto = handler.execute({
                'seller_id': seller_id,
                'status': status,
                'limit': limit,
                'offset': offset
            })
            
            return jsonify([
                order.to_dict() if hasattr(order, 'to_dict') else order
                for order in orders_dto
            ]), 200
        
        except Exception as e:
            logger.error(f"Error fetching seller orders: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    @order_bp.route('/pending', methods=['GET'])
    def get_pending_orders():
        """Get all pending orders (admin dashboard)"""
        try:
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            logger.info(f"Fetching pending orders")
            
            handler = container.get('list_pending_orders_handler')
            orders_dto = handler.execute({'limit': limit, 'offset': offset})
            
            return jsonify([
                order.to_dict() if hasattr(order, 'to_dict') else order
                for order in orders_dto
            ]), 200
        
        except Exception as e:
            logger.error(f"Error fetching pending orders: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    
    return order_bp
