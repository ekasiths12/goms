import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql://GOMS:PGOMS@localhost/garment_db'
    
    # Handle Railway MySQL URL format
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('mysql://'):
        # Railway uses mysql:// but SQLAlchemy expects mysql+pymysql://
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('mysql://', 'mysql+pymysql://', 1)
        
        # Add connection parameters for Railway
        if '?' not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += '?charset=utf8mb4'
        else:
            SQLALCHEMY_DATABASE_URI += '&charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # AWS S3 configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')
    
    # PDF storage configuration (now in S3)
    PDF_FOLDER = 'pdfs'
    
    # Image storage configuration (now in S3)
    IMAGE_FOLDER = 'images'
    
    # Application settings
    ITEMS_PER_PAGE = 50
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://GOMS:PGOMS@localhost/garment_db'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Railway.app will provide DATABASE_URL environment variable

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
