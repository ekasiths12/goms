from extensions import db
from datetime import datetime
import os

class Image(db.Model):
    """Image model for storing garment images"""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)  # Now stores S3 key
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stitching_invoices = db.relationship('StitchingInvoice', backref='image', lazy=True)
    
    def __repr__(self):
        return f'<Image {self.file_path}>'
    
    def to_dict(self):
        """Convert image to dictionary"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'filename': self.file_path.split('/')[-1] if self.file_path else None,
            'image_url': self.get_image_url()
        }
    
    @classmethod
    def get_by_file_path(cls, file_path):
        """Get image by file path (S3 key)"""
        return cls.query.filter_by(file_path=file_path).first()
    
    def get_image_url(self):
        """Get the image URL for storage service"""
        if self.file_path:
            from app.services.storage_service_factory import StorageServiceFactory
            try:
                storage_service = StorageServiceFactory.get_storage_service()
                return storage_service.get_file_url(self.file_path)
            except:
                # Fallback to direct URL if service not available
                return f"/static/{self.file_path}"
        return None
    
    def get_image_path_for_pdf(self):
        """Get image path suitable for PDF generation"""
        if self.file_path:
            from app.services.storage_service_factory import StorageServiceFactory
            try:
                storage_service = StorageServiceFactory.get_storage_service()
                
                # For local storage, return the direct path
                if hasattr(storage_service, 'base_path'):
                    # Local storage service
                    full_path = storage_service.base_path / self.file_path
                    if full_path.exists():
                        return str(full_path)
                
                # For S3 storage, download to temp location
                temp_dir = '/tmp'
                os.makedirs(temp_dir, exist_ok=True)
                temp_file_path = os.path.join(temp_dir, f"temp_image_{self.id}_{os.path.basename(self.file_path)}")
                
                # Download from storage to temp location
                if storage_service.download_file(self.file_path, temp_file_path):
                    return temp_file_path
                else:
                    return None
            except Exception as e:
                print(f"Error getting image path for PDF: {e}")
                return None
        return None
