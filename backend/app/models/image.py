from extensions import db
from datetime import datetime
import os

class Image(db.Model):
    """Image model for storing garment images"""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Google Drive fields (commented out - not in current database schema)
    # google_drive_id = db.Column(db.String(255), nullable=True)
    # google_drive_link = db.Column(db.String(500), nullable=True)
    # google_drive_filename = db.Column(db.String(255), nullable=True)
    
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
            # Google Drive fields not included - not in current database schema
        }
    
    @classmethod
    def get_by_file_path(cls, file_path):
        """Get image by file path"""
        return cls.query.filter_by(file_path=file_path).first()
    
    @classmethod
    def get_by_google_drive_id(cls, google_drive_id):
        """Get image by Google Drive ID"""
        return cls.query.filter_by(google_drive_id=google_drive_id).first()
    
    def get_image_url(self):
        """Get the best available image URL (Google Drive preferred, fallback to local)"""
        try:
            if hasattr(self, 'google_drive_link') and self.google_drive_link:
                return self.google_drive_link
        except:
            pass
        
        if self.file_path:
            # Return local file path if Google Drive not available
            return self.file_path
        return None
    
    def get_image_path_for_pdf(self):
        """Get image path suitable for PDF generation (prefer local, fallback to Google Drive)"""
        if self.file_path and os.path.exists(self.file_path):
            return self.file_path
        
        try:
            if hasattr(self, 'google_drive_link') and self.google_drive_link:
                # For PDF generation, we might need to download from Google Drive
                # For now, return the local path if it exists
                return self.file_path
        except:
            pass
        
        return None
