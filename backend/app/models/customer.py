from extensions import db
from datetime import datetime

class Customer(db.Model):
    """Customer model for storing customer information"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(50), unique=True, nullable=False)
    short_name = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(255))
    registration_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='customer', lazy=True)
    packing_lists = db.relationship('PackingList', backref='customer', lazy=True)
    group_bills = db.relationship('StitchingInvoiceGroup', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.short_name}>'
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'short_name': self.short_name,
            'full_name': self.full_name,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def get_by_customer_id(cls, customer_id):
        """Get customer by customer_id"""
        return cls.query.filter_by(customer_id=customer_id).first()
    
    @classmethod
    def get_by_short_name(cls, short_name):
        """Get customer by short_name"""
        return cls.query.filter_by(short_name=short_name).first()
    
    @classmethod
    def get_active_customers(cls):
        """Get all active customers"""
        return cls.query.filter_by(is_active=True).order_by(cls.short_name).all()
