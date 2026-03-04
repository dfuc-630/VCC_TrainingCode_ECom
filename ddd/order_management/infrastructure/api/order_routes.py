from flask import Blueprint, request, jsonify
from ddd.order_management.domain.exceptions import OrderNotFoundError


def create_order_routes(container):
    """
    Create Flask blueprint for order routes
    
    Args:
        container: DI container with all handlers
        
    Returns:
        Blueprint with order endpoints
    """
    order_bp = Blueprint('order_api', __name__, url_prefix='/orders')
    
    @order_bp.route('', methods=['POST'])
    def create_order():
        """Create new order"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required = ['customer_id', 'seller_id', 'items', 'shipping_address', 'shipping_phone']
            if not all(field in data for field in required):
                return jsonify({'error': f'Missing required fields: {", ".join(required)}'}), 400
            
            # Convert items
            from ddd.order_management.application.commands.create_order_command import (
                CreateOrderCommand,
                CreateOrderItemCommand,
            )
            
            items = [
                CreateOrderItemCommand(
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                )
                for item in data['items']
            ]
            
            command = CreateOrderCommand(
                customer_id=data['customer_id'],
                seller_id=data['seller_id'],
                items=items,
                shipping_address=data['shipping_address'],
                shipping_phone=data['shipping_phone'],
            )
            
            # Execute via handler
            handler = container.get('create_order_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 201
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/<order_id>', methods=['GET'])
    def get_order(order_id):
        """Get order details"""
        try:
            from ddd.order_management.application.queries.get_order_query import GetOrderQuery
            
            query = GetOrderQuery(order_id=order_id)
            handler = container.get('get_order_handler')
            order_dto = handler.execute(query)
            
            if not order_dto:
                return jsonify({'error': 'Order not found'}), 404
            
            return jsonify(order_dto.to_dict()), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/<order_id>/confirm', methods=['POST'])
    def confirm_order(order_id):
        """Confirm order"""
        try:
            from ddd.order_management.application.commands.create_order_command import ConfirmOrderCommand
            
            command = ConfirmOrderCommand(order_id=order_id)
            handler = container.get('confirm_order_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except OrderNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/<order_id>/ship', methods=['POST'])
    def ship_order(order_id):
        """Ship order"""
        try:
            from ddd.order_management.application.commands.create_order_command import ShipOrderCommand
            
            data = request.get_json()
            seller_id = data.get('seller_id')
            
            command = ShipOrderCommand(order_id=order_id, seller_id=seller_id)
            handler = container.get('ship_order_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except OrderNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/<order_id>/complete', methods=['POST'])
    def complete_order(order_id):
        """Complete order"""
        try:
            from ddd.order_management.application.commands.create_order_command import CompleteOrderCommand
            
            command = CompleteOrderCommand(order_id=order_id)
            handler = container.get('complete_order_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except OrderNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/<order_id>/cancel', methods=['POST'])
    def cancel_order(order_id):
        """Cancel order"""
        try:
            from ddd.order_management.application.commands.create_order_command import CancelOrderCommand
            
            data = request.get_json()
            customer_id = data.get('customer_id')
            
            command = CancelOrderCommand(order_id=order_id, customer_id=customer_id)
            handler = container.get('cancel_order_handler')
            result = handler.execute(command)
            
            return jsonify(result.to_dict()), 200
        
        except OrderNotFoundError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @order_bp.route('/customer/<customer_id>', methods=['GET'])
    def get_customer_orders(customer_id):
        """Get all orders for customer"""
        try:
            from ddd.order_management.application.queries.get_order_query import GetCustomerOrdersQuery
            
            status = request.args.get('status')
            query = GetCustomerOrdersQuery(customer_id=customer_id, status=status)
            handler = container.get('get_customer_orders_handler')
            orders_dto = handler.execute(query)
            
            return jsonify([order.to_dict() for order in orders_dto]), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return order_bp
