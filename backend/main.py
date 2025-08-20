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
        return {'status': 'healthy', 'message': 'Garment Management System API is running'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8000)
