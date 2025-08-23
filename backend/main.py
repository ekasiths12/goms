from flask import Flask, request, redirect, send_from_directory
from flask_cors import CORS
from config.config import Config
from extensions import db
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_app(config_class=Config):
    """Application factory pattern"""
    # Determine static folder path based on environment
    print(f"🔍 Debugging static folder detection...")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   ../frontend exists: {os.path.exists('../frontend')}")
    print(f"   ./frontend exists: {os.path.exists('frontend')}")
    print(f"   ./frontend/ exists: {os.path.exists('./frontend/')}")
    
    if os.path.exists('../frontend'):
        # Local development - frontend is in parent directory
        static_folder = '../frontend'
        print(f"   Using ../frontend for local development")
    elif os.path.exists('frontend'):
        # Railway deployment - frontend is copied to backend directory
        static_folder = 'frontend'
        print(f"   Using ./frontend for Railway deployment")
    else:
        # Fallback - use current directory
        static_folder = '.'
        print(f"   Using current directory as fallback")
    
    print(f"   Final static_folder: {static_folder}")
    
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    app.config.from_object(config_class)
    
    # Disable automatic trailing slash redirects to prevent CORS issues
    app.url_map.strict_slashes = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS for local development and production
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:8000", "http://127.0.0.1:8000"], 
         supports_credentials=True, 
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'Accept', 'Cache-Control', 'Pragma'],
         expose_headers=['Content-Type', 'Authorization'])
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:8000", "http://127.0.0.1:8000"]:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Cache-Control,Pragma')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.invoices import invoices_bp
    from app.routes.stitching import stitching_bp
    from app.routes.packing_lists import packing_lists_bp
    from app.routes.group_bills import group_bills_bp
    from app.routes.customers import customers_bp
    from app.routes.files import files_bp
    from app.routes.images import images_bp
    from app.routes.debug.database_inspector import debug_bp
    from app.routes.debug.schema_comparison import schema_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    app.register_blueprint(stitching_bp, url_prefix='/api/stitching')
    app.register_blueprint(packing_lists_bp, url_prefix='/api/packing-lists')
    app.register_blueprint(group_bills_bp, url_prefix='/api/group-bills')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(debug_bp)
    app.register_blueprint(schema_bp)
    
    # Test route
    @app.route('/test')
    def test():
        import os
        return {
            'message': 'Flask app is working', 
            'status': 'ok',
            'static_folder': app.static_folder,
            'static_exists': os.path.exists(app.static_folder),
            'frontend_files': os.listdir(app.static_folder) if os.path.exists(app.static_folder) else []
        }
    
    # Debug route to log all requests
    @app.route('/debug/request')
    def debug_request():
        return {
            'method': request.method,
            'url': request.url,
            'path': request.path,
            'headers': dict(request.headers),
            'args': dict(request.args)
        }
    
    # Debug route to check static folder configuration
    @app.route('/debug/static')
    def debug_static():
        import os
        static_folder = app.static_folder
        static_exists = os.path.exists(static_folder)
        static_contents = []
        if static_exists:
            try:
                static_contents = os.listdir(static_folder)
            except Exception as e:
                static_contents = [f"Error listing directory: {str(e)}"]
        
        # Check if specific files exist
        fabric_invoices_exists = os.path.exists(os.path.join(static_folder, 'fabric-invoices.html'))
        login_exists = os.path.exists(os.path.join(static_folder, 'login.html'))
        
        return {
            'static_folder': static_folder,
            'static_exists': static_exists,
            'static_contents': static_contents,
            'fabric_invoices_exists': fabric_invoices_exists,
            'login_exists': login_exists,
            'current_dir': os.getcwd(),
            'current_dir_contents': os.listdir('.') if os.path.exists('.') else []
        }
    
    # Debug route to check if specific files exist
    @app.route('/debug/file/<path:filename>')
    def debug_file(filename):
        import os
        file_path = os.path.join(app.static_folder, filename)
        exists = os.path.exists(file_path)
        return {
            'filename': filename,
            'file_path': file_path,
            'exists': exists,
            'static_folder': app.static_folder
        }
    
    # Force HTTPS redirects in production only
    @app.before_request
    def force_https():
        # Skip HTTPS redirect for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        # Only redirect in production, not in development
        if not app.debug and request.headers.get('X-Forwarded-Proto') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            print(f"🔄 HTTPS redirect: {request.url} -> {url}")
            return redirect(url, code=301)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        try:
            # Test database connection using new SQLAlchemy syntax
            with db.engine.connect() as connection:
                result = connection.execute(db.text('SELECT 1'))
                result.close()
            db_status = 'connected'
        except Exception as e:
            db_status = f'disconnected: {str(e)[:50]}'
        
        return {
            'status': 'healthy', 
            'message': 'Garment Management System API is running',
            'database': db_status
        }
    
    # Frontend routes - serve HTML pages (specific routes first)
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'login.html')
    
    @app.route('/login.html')
    def login():
        return send_from_directory(app.static_folder, 'login.html')
    
    @app.route('/login')
    def login_no_ext():
        return send_from_directory(app.static_folder, 'login.html')
    
    @app.route('/fabric-invoices.html')
    def fabric_invoices():
        return send_from_directory(app.static_folder, 'fabric-invoices.html')
    
    @app.route('/fabric-invoices')
    def fabric_invoices_no_ext():
        import os
        file_path = os.path.join(app.static_folder, 'fabric-invoices.html')
        exists = os.path.exists(file_path)
        print(f"🔍 fabric-invoices route debug:")
        print(f"   static_folder: {app.static_folder}")
        print(f"   file_path: {file_path}")
        print(f"   exists: {exists}")
        if not exists:
            return f"File not found: {file_path}", 404
        return send_from_directory(app.static_folder, 'fabric-invoices.html')
    
    @app.route('/stitching-records.html')
    def stitching_records():
        return send_from_directory(app.static_folder, 'stitching-records.html')
    
    @app.route('/stitching-records')
    def stitching_records_no_ext():
        return send_from_directory(app.static_folder, 'stitching-records.html')
    
    @app.route('/packing-lists.html')
    def packing_lists():
        return send_from_directory(app.static_folder, 'packing-lists.html')
    
    @app.route('/packing-lists')
    def packing_lists_no_ext():
        return send_from_directory(app.static_folder, 'packing-lists.html')
    
    @app.route('/group-bills.html')
    def group_bills():
        return send_from_directory(app.static_folder, 'group-bills.html')
    
    @app.route('/group-bills')
    def group_bills_no_ext():
        return send_from_directory(app.static_folder, 'group-bills.html')
    
    @app.route('/index.html')
    def index_html():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/index')
    def index_no_ext():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/debug.html')
    def debug():
        return send_from_directory(app.static_folder, 'debug.html')
    
    @app.route('/debug')
    def debug_no_ext():
        return send_from_directory(app.static_folder, 'debug.html')
    
    # Database initialization endpoint
    @app.route('/api/init-db')
    def init_database():
        try:
            # Import specific models instead of using import *
            from app.models.customer import Customer
            from app.models.invoice import Invoice, InvoiceLine
            from app.models.stitching import StitchingInvoice, GarmentFabric, LiningFabric
            from app.models.packing_list import PackingList, PackingListLine
            from app.models.group_bill import StitchingInvoiceGroup, StitchingInvoiceGroupLine
            from app.models.image import Image
            from app.models.serial_counter import SerialCounter
            
            # Create all tables
            db.create_all()
            
            # Initialize serial counters
            serial_types = ['ST', 'GB', 'PL', 'GBN']
            for serial_type in serial_types:
                counter = SerialCounter.get_or_create(serial_type)
            
            return {
                'status': 'success',
                'message': 'Database initialized successfully',
                'tables_created': True,
                'serial_counters': serial_types
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database initialization failed: {str(e)}'
            }, 500
    
    # Catch-all route for any other frontend files (must be last)
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        return send_from_directory(app.static_folder, filename)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Ensure app context is available
    with app.app_context():
        # Test database connection
        try:
            db.engine.connect()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("💡 Make sure MySQL is running and database is accessible")
    
    app.run(debug=False, host='0.0.0.0', port=8000)
