import pytest


class TestSellerProducts:
    """Test seller product management"""
    
    def test_get_products_success(self, client, seller_headers, product):
        """Test get seller's products"""
        response = client.get('/api/seller/products',
                            headers=seller_headers)
        
        assert response.status_code == 200
        assert 'products' in response.json
        assert len(response.json['products']) == 1
    
    def test_create_product_success(self, client, seller_headers, category):
        """Test create product"""
        response = client.post('/api/seller/products',
                              headers=seller_headers,
                              json={
                                  'name': 'Samsung Galaxy S24',
                                  'description': 'Latest Samsung phone',
                                  'category_id': category.id,
                                  'current_price': 25990000.00,
                                  'original_price': 28990000.00,
                                  'stock_quantity': 20,
                                  'image_url': 'https://example.com/samsung.jpg'
                              })
        
        assert response.status_code == 201
        assert 'product' in response.json
        assert response.json['product']['name'] == 'Samsung Galaxy S24'
        assert response.json['product']['slug'] == 'samsung-galaxy-s24'
    
    def test_create_product_missing_fields(self, client, seller_headers):
        """Test create product with missing fields"""
        response = client.post('/api/seller/products',
                              headers=seller_headers,
                              json={
                                  'name': 'Test Product'
                              })
        
        assert response.status_code == 400
    
    def test_create_product_wrong_role(self, client, customer_headers):
        """Test create product as customer (should fail)"""
        response = client.post('/api/seller/products',
                              headers=customer_headers,
                              json={
                                  'name': 'Test Product',
                                  'current_price': 100000.00,
                                  'stock_quantity': 10
                              })
        
        assert response.status_code == 403
    
    def test_get_product_detail_success(self, client, seller_headers, product):
        """Test get product detail"""
        response = client.get(f'/api/seller/products/{product.id}',
                            headers=seller_headers)
        
        assert response.status_code == 200
        assert 'product' in response.json
    
    def test_update_product_success(self, client, seller_headers, product):
        """Test update product"""
        response = client.put(f'/api/seller/products/{product.id}',
                            headers=seller_headers,
                            json={
                                'name': 'iPhone 15 Pro Max Updated',
                                'current_price': 27990000.00,
                                'stock_quantity': 15
                            })
        
        assert response.status_code == 200
        assert response.json['product']['name'] == 'iPhone 15 Pro Max Updated'
        assert response.json['product']['current_price'] == 27990000.00
    
    def test_update_product_not_found(self, client, seller_headers):
        """Test update non-existent product"""
        response = client.put('/api/seller/products/invalid-id',
                            headers=seller_headers,
                            json={'name': 'Updated'})
        
        assert response.status_code == 404
    
    def test_delete_product_success(self, client, seller_headers, product):
        """Test delete product (soft delete)"""
        response = client.delete(f'/api/seller/products/{product.id}',
                               headers=seller_headers)
        
        assert response.status_code == 200
        
        # Verify product is soft deleted
        from app.models.product import Product
        deleted_product = Product.query.get(product.id)
        assert deleted_product.is_deleted is True
    
    def test_delete_product_not_found(self, client, seller_headers):
        """Test delete non-existent product"""
        response = client.delete('/api/seller/products/invalid-id',
                               headers=seller_headers)
        
        assert response.status_code == 404