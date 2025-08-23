from extensions import db
from datetime import datetime

class CustomerIdMapping(db.Model):
    """Model for storing customer ID mappings with short names"""
    __tablename__ = 'customer_id_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), unique=True, nullable=False)
    short_name = db.Column(db.String(50), nullable=True)  # Can be null initially
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomerIdMapping {self.customer_id}: {self.short_name}>'
    
    def to_dict(self):
        """Convert mapping to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'short_name': self.short_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_customer_id(cls, customer_id):
        """Get mapping by customer_id"""
        return cls.query.filter_by(customer_id=customer_id).first()
    
    @classmethod
    def get_all_mappings(cls):
        """Get all customer ID mappings"""
        return cls.query.order_by(cls.customer_id).all()
    
    @classmethod
    def create_or_update(cls, customer_id, short_name=None):
        """Create or update a customer ID mapping"""
        mapping = cls.get_by_customer_id(customer_id)
        if mapping:
            # Only update short_name if it's provided and current short_name is empty
            if short_name and not mapping.short_name:
                mapping.short_name = short_name
                mapping.updated_at = datetime.utcnow()
        else:
            mapping = cls(customer_id=customer_id, short_name=short_name)
            db.session.add(mapping)
        
        db.session.flush()
        return mapping
