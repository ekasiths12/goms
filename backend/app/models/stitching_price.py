from extensions import db
from datetime import datetime

class StitchingPrice(db.Model):
    """StitchingPrice model for memorizing stitching prices by garment and customer"""
    __tablename__ = 'stitching_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    garment_name = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='stitching_prices')
    
    # Composite unique constraint to ensure one price per garment-customer combination
    __table_args__ = (
        db.UniqueConstraint('garment_name', 'customer_id', name='unique_garment_customer_price'),
    )
    
    def __repr__(self):
        return f'<StitchingPrice {self.garment_name} - {self.customer.short_name if self.customer else "Unknown"}: {self.price}>'
    
    def to_dict(self):
        """Convert stitching price to dictionary"""
        return {
            'id': self.id,
            'garment_name': self.garment_name,
            'customer_id': self.customer_id,
            'customer_name': self.customer.short_name if self.customer else None,
            'customer_full_name': self.customer.full_name if self.customer else None,
            'price': float(self.price) if self.price else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_garment_and_customer(cls, garment_name, customer_id):
        """Get memorized price for a specific garment and customer combination"""
        return cls.query.filter_by(
            garment_name=garment_name,
            customer_id=customer_id
        ).first()
    
    @classmethod
    def get_all_prices(cls):
        """Get all memorized prices ordered by garment name and customer"""
        return cls.query.join(Customer).order_by(cls.garment_name, Customer.short_name).all()
    
    @classmethod
    def create_or_update_price(cls, garment_name, customer_id, price):
        """Create or update price for a garment-customer combination"""
        existing_price = cls.get_by_garment_and_customer(garment_name, customer_id)
        
        if existing_price:
            existing_price.price = price
            existing_price.updated_at = datetime.utcnow()
            db.session.flush()
            return existing_price
        else:
            new_price = cls(
                garment_name=garment_name,
                customer_id=customer_id,
                price=price
            )
            db.session.add(new_price)
            db.session.flush()
            return new_price
