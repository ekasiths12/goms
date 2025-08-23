from extensions import db
from datetime import datetime

class DeliveryLocation(db.Model):
    __tablename__ = 'delivery_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_all_locations(cls):
        """Get all delivery locations ordered by name"""
        return cls.query.order_by(cls.name).all()
    
    @classmethod
    def get_by_name(cls, name):
        """Get delivery location by name"""
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def create_location(cls, name):
        """Create a new delivery location"""
        location = cls(name=name)
        db.session.add(location)
        db.session.flush()
        return location
    
    @classmethod
    def delete_location(cls, location_id):
        """Delete a delivery location by ID"""
        location = cls.query.get(location_id)
        if location:
            db.session.delete(location)
            db.session.flush()
            return True
        return False
