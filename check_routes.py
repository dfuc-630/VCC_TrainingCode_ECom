from integration.flask_app import create_ddd_app

try:
    app = create_ddd_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db', 'DEBUG': True})
    print("✓ App created successfully!\n")
    
    routes = [(str(r.rule), sorted(r.methods)) for r in app.url_map.iter_rules()]
    api_routes = [r for r in routes if 'api' in r[0]]
    
    print(f"Total routes: {len(routes)}")
    print(f"API routes: {len(api_routes)}\n")
    
    print("Registered API routes:")
    for rule, methods in sorted(api_routes):
        methods_str = ','.join([m for m in methods if m not in ['OPTIONS', 'HEAD']])
        print(f"  {methods_str:6s} {rule}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
