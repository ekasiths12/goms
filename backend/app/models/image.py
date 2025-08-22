from extensions import db
from datetime import datetime
import os

class Image(db.Model):
    """Image model for storing garment images"""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Google Drive fields removed - using Railway volume storage instead
    
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
            'filename': self.file_path.split('/')[-1] if self.file_path else None
            # Google Drive fields removed - using Railway volume storage instead
        }
    
    @classmethod
    def get_by_file_path(cls, file_path):
        """Get image by file path"""
        return cls.query.filter_by(file_path=file_path).first()
    
    def get_image_url(self):
        """Get the image URL for Railway volume storage"""
        if self.file_path:
            return f"/static/{self.file_path}"
        return None
    
    def get_image_path_for_pdf(self):
        """Get image path suitable for PDF generation"""
        if self.file_path:
            # For Railway volume storage, we need to get the absolute path
            from app.services.file_storage_service import FileStorageService
            try:
                storage_service = FileStorageService()
                return storage_service.get_file_path(self.file_path)
            except:
                # Fallback to relative path
                return self.file_path
        return None
