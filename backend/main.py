from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config.config import Config
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize extensions
db = SQLAlchemy()

# Make db available to other modules
def get_db():
    return db

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.invoices import invoices_bp
    from app.routes.stitching import stitching_bp
    from app.routes.packing_lists import packing_lists_bp
    from app.routes.group_bills import group_bills_bp
    from app.routes.customers import customers_bp
    from app.routes.files import files_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    app.register_blueprint(stitching_bp, url_prefix='/api/stitching')
    app.register_blueprint(packing_lists_bp, url_prefix='/api/packing-lists')
    app.register_blueprint(group_bills_bp, url_prefix='/api/group-bills')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        try:
            # Test database connection
            db.engine.execute('SELECT 1')
            db_status = 'connected'
        except Exception as e:
            db_status = f'disconnected: {str(e)[:50]}'
        
        return {
            'status': 'healthy', 
            'message': 'Garment Management System API is running',
            'database': db_status
        }
    
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8000)
