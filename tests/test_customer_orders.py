import pytest
from decimal import Decimal


class TestCustomerOrders:
    """Test customer order operations"""
    
    def test_create_order_success(self, client, customer_headers, product):
        """Test successful order creation"""
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [
                                      {
                                          'product_id': product.id,
                                          'quantity': 2
                                      }
                                  ],
                                  'shipping_address': '123 Test St, Hanoi',
                                  'shipping_phone': '0901234567'
                              })
        
        assert response.status_code == 201
        assert 'order' in response.json
        assert response.json['order']['total_amount'] == 59980000.00
        assert response.json['order']['status'] == 'pending'
        assert response.json['order']['payment_status'] == 'paid'
        assert len(response.json['order']['items']) == 1
    
    def test_create_order_insufficient_balance(self, client, customer_user, customer_headers, product):
        """Test order creation with insufficient balance"""
        # Reduce wallet balance
        from app.models.wallet import Wallet
        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        wallet.balance = Decimal('1000.00')
        db.session.commit()
        
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [
                                      {
                                          'product_id': product.id,
                                          'quantity': 1
                                      }
                                  ],
                                  'shipping_address': '123 Test St',
                                  'shipping_phone': '0901234567'
                              })
        
        assert response.status_code == 400
        assert 'Insufficient balance' in response.json['error']
    
    def test_create_order_insufficient_stock(self, client, customer_headers, product):
        """Test order creation with insufficient stock"""
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [
                                      {
                                          'product_id': product.id,
                                          'quantity': 100
                                      }
                                  ],
                                  'shipping_address': '123 Test St',
                                  'shipping_phone': '0901234567'
                              })
        
        assert response.status_code == 400
        assert 'Insufficient stock' in response.json['error']
    
    def test_create_order_product_not_found(self, client, customer_headers):
        """Test order creation with non-existent product"""
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [
                                      {
                                          'product_id': 'invalid-id',
                                          'quantity': 1
                                      }
                                  ],
                                  'shipping_address': '123 Test St',
                                  'shipping_phone': '0901234567'
                              })
        
        assert response.status_code == 400
    
    def test_create_order_empty_items(self, client, customer_headers):
        """Test order creation with empty items"""
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [],
                                  'shipping_address': '123 Test St',
                                  'shipping_phone': '0901234567'
                              })
        
        assert response.status_code == 400
    
    def test_create_order_missing_fields(self, client, customer_headers, product):
        """Test order creation with missing fields"""
        response = client.post('/api/customer/orders',
                              headers=customer_headers,
                              json={
                                  'items': [
                                      {
                                          'product_id': product.id,
                                          'quantity': 1
                                      }
                                  ]
                              })
        
        assert response.status_code == 400
    
    def test_get_orders_success(self, client, customer_headers, product):
        """Test get customer orders"""
        # Create an order first
        client.post('/api/customer/orders',
                   headers=customer_headers,
                   json={
                       'items': [{'product_id': product.id, 'quantity': 1}],
                       'shipping_address': '123 Test St',
                       'shipping_phone': '0901234567'
                   })
        
        response = client.get('/api/customer/orders',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert 'orders' in response.json
        assert len(response.json['orders']) == 1
    
    def test_get_orders_filter_by_status(self, client, customer_headers, product):
        """Test get orders filtered by status"""
        response = client.get('/api/customer/orders?status=pending',
                            headers=customer_headers)
        
        assert response.status_code == 200
    
    def test_get_order_detail_success(self, client, customer_headers, product):
        """Test get order detail"""
        # Create order
        create_response = client.post('/api/customer/orders',
                                     headers=customer_headers,
                                     json={
                                         'items': [{'product_id': product.id, 'quantity': 1}],
                                         'shipping_address': '123 Test St',
                                         'shipping_phone': '0901234567'
                                     })
        order_id = create_response.json['order']['id']
        
        # Update status
        response = client.put(f'/api/seller/orders/{order_id}/status',
                            headers=seller_headers,
                            json={'status': 'confirmed'})
        
        assert response.status_code == 200
        assert response.json['order']['status'] == 'confirmed'
    
    def test_update_order_status_invalid_transition(self, client, seller_headers, customer_headers, product):
        """Test invalid status transition"""
        # Create order
        create_response = client.post('/api/customer/orders',
                                     headers=customer_headers,
                                     json={
                                         'items': [{'product_id': product.id, 'quantity': 1}],
                                         'shipping_address': '123 Test St',
                                         'shipping_phone': '0901234567'
                                     })
        order_id = create_response.json['order']['id']
        
        # Try invalid transition (pending -> completed)
        response = client.put(f'/api/seller/orders/{order_id}/status',
                            headers=seller_headers,
                            json={'status': 'completed'})
        
        assert response.status_code == 400
    
    def test_get_revenue_success(self, client, seller_headers):
        """Test get seller revenue"""
        response = client.get('/api/seller/revenue',
                            headers=seller_headers)
        
        assert response.status_code == 200
        assert 'total_revenue' in response.json
        assert 'total_orders' in response.json
        assert 'completed_orders' in response.json
        assert 'pending_orders' in response.json