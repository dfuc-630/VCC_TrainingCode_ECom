import pytest


class TestCustomerProducts:
    """Test customer product browsing"""
    
    def test_search_products_success(self, client, customer_headers, product):
        """Test search products"""
        response = client.get('/api/customer/products',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert 'products' in response.json
        assert len(response.json['products']) == 1
        assert response.json['products'][0]['name'] == 'iPhone 15 Pro Max'
    
    def test_search_products_by_name(self, client, customer_headers, product):
        """Test search products by name"""
        response = client.get('/api/customer/products?search=iPhone',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert len(response.json['products']) == 1
    
    def test_search_products_no_results(self, client, customer_headers, product):
        """Test search products with no results"""
        response = client.get('/api/customer/products?search=Samsung',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert len(response.json['products']) == 0
    
    def test_search_products_by_category(self, client, customer_headers, product, category):
        """Test search products by category"""
        response = client.get(f'/api/customer/products?category_id={category.id}',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert len(response.json['products']) == 1
    
    def test_search_products_pagination(self, client, customer_headers, product):
        """Test products pagination"""
        response = client.get('/api/customer/products?page=1&per_page=10',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert response.json['page'] == 1
        assert 'pages' in response.json
    
    def test_get_product_detail_success(self, client, customer_headers, product):
        """Test get product detail"""
        response = client.get(f'/api/customer/products/{product.id}',
                            headers=customer_headers)
        
        assert response.status_code == 200
        assert 'product' in response.json
        assert response.json['product']['name'] == 'iPhone 15 Pro Max'
        assert response.json['product']['current_price'] == 29990000.00
    
    def test_get_product_not_found(self, client, customer_headers):
        """Test get non-existent product"""
        response = client.get('/api/customer/products/invalid-id',
                            headers=customer_headers)
        
        assert response.status_code == 404
    
    def test_get_inactive_product(self, client, customer_headers, product):
        """Test get inactive product (should fail)"""
        product.is_active = False
        db.session.commit()
        
        response = client.get(f'/api/customer/products/{product.id}',
                            headers=customer_headers)
        
        assert response.status_code == 404