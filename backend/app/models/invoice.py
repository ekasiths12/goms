from extensions import db
from datetime import datetime

class Invoice(db.Model):
    """Invoice model for storing fabric invoice headers"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(32), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    invoice_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='open')
    tax_invoice_number = db.Column(db.String(50))
    
    # Relationships
    invoice_lines = db.relationship('InvoiceLine', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def to_dict(self):
        """Convert invoice to dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.short_name if self.customer else None,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'status': self.status,
            'tax_invoice_number': self.tax_invoice_number,
            'line_count': len(self.invoice_lines)
        }
    
    def calculate_total(self):
        """Calculate total amount from invoice lines"""
        total = sum(line.unit_price * line.yards_sent for line in self.invoice_lines)
        self.total_amount = total
        return total
    
    @classmethod
    def get_by_invoice_number(cls, invoice_number):
        """Get invoice by invoice number"""
        return cls.query.filter_by(invoice_number=invoice_number).first()
    
    @classmethod
    def get_by_customer(cls, customer_id):
        """Get all invoices for a customer"""
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.invoice_date.desc()).all()

class InvoiceLine(db.Model):
    """InvoiceLine model for storing individual invoice line items"""
    __tablename__ = 'invoice_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=0)  # Legacy field
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    delivered_location = db.Column(db.String(255))
    is_defective = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(100))
    delivery_note = db.Column(db.String(255))
    yards_sent = db.Column(db.Numeric(10, 2), default=0)
    yards_consumed = db.Column(db.Numeric(10, 2), default=0)
    
    # Commission sales are now tracked in separate CommissionSale model
    
    # Relationships
    stitching_invoices = db.relationship('StitchingInvoice', backref='invoice_line', lazy=True)
    garment_fabrics = db.relationship('GarmentFabric', backref='invoice_line', lazy=True)
    
    def __repr__(self):
        return f'<InvoiceLine {self.item_name} - {self.invoice.invoice_number}>'
    
    def to_dict(self):
        """Convert invoice line to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else None,
            'customer_name': self.invoice.customer.short_name if self.invoice and self.invoice.customer else None,
            'item_name': self.item_name,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'delivered_location': self.delivered_location,
            'is_defective': self.is_defective,
            'color': self.color,
            'delivery_note': self.delivery_note,
            'yards_sent': float(self.yards_sent) if self.yards_sent else 0,
            'yards_consumed': float(self.yards_consumed) if self.yards_consumed else 0,
            'pending_yards': float(self.pending_yards),
            'total_value': float(self.unit_price * self.yards_sent) if self.unit_price and self.yards_sent else 0,
            'total_commission_yards': sum(float(cs.yards_sold) for cs in self.commission_sales),
            'total_commission_amount': sum(float(cs.commission_amount) for cs in self.commission_sales),
            'commission_sales_count': len(self.commission_sales)
        }
    
    @property
    def pending_yards(self):
        """Calculate pending yards (excluding commission sales)"""
        total_commission_yards = sum(cs.yards_sold for cs in self.commission_sales)
        consumed = (self.yards_consumed or 0) + total_commission_yards
        return (self.yards_sent or 0) - consumed
    
    @property
    def total_value(self):
        """Calculate total value"""
        return (self.unit_price or 0) * (self.yards_sent or 0)
    
    @classmethod
    def get_available_fabrics(cls):
        """Get all invoice lines with pending yards > 0"""
        return cls.query.filter(
            cls.yards_sent > cls.yards_consumed
        ).order_by(cls.invoice_id.desc()).all()
    
    @classmethod
    def get_by_item_name(cls, item_name):
        """Get invoice lines by item name"""
        return cls.query.filter_by(item_name=item_name).all()
    
    @classmethod
    def get_commission_sales(cls):
        """Get all invoice lines that have commission sales"""
        return cls.query.filter(cls.commission_sales.any()).all()


class FabricInventory(db.Model):
    """FabricInventory model for tracking fabric consumption and inventory"""
    __tablename__ = 'fabric_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=True)
    total_delivered = db.Column(db.Numeric(10, 2), default=0)
    total_consumed = db.Column(db.Numeric(10, 2), default=0)
    total_defective = db.Column(db.Numeric(10, 2), default=0)
    pending_amount = db.Column(db.Numeric(10, 2), default=0)
    
    def __repr__(self):
        return f'<FabricInventory {self.item_name}>'
    
    def to_dict(self):
        """Convert fabric inventory to dictionary"""
        return {
            'id': self.id,
            'item_name': self.item_name,
            'total_delivered': float(self.total_delivered) if self.total_delivered else 0,
            'total_consumed': float(self.total_consumed) if self.total_consumed else 0,
            'total_defective': float(self.total_defective) if self.total_defective else 0,
            'pending_amount': float(self.pending_amount) if self.pending_amount else 0
        }
    
    @property
    def available_yards(self):
        """Calculate available yards"""
        return (self.total_delivered or 0) - (self.total_consumed or 0) - (self.total_defective or 0)
    
    @classmethod
    def get_by_item_name(cls, item_name):
        """Get fabric inventory by item name"""
        return cls.query.filter_by(item_name=item_name).first()
    
    @classmethod
    def update_inventory(cls, item_name, delivered=0, consumed=0, defective=0):
        """Update fabric inventory for an item"""
        inventory = cls.get_by_item_name(item_name)
        
        if not inventory:
            inventory = cls(
                item_name=item_name,
                total_delivered=delivered,
                total_consumed=consumed,
                total_defective=defective,
                pending_amount=delivered - consumed - defective
            )
            db.session.add(inventory)
        else:
            inventory.total_delivered = float(inventory.total_delivered or 0) + delivered
            inventory.total_consumed = float(inventory.total_consumed or 0) + consumed
            inventory.total_defective = float(inventory.total_defective or 0) + defective
            inventory.pending_amount = float(inventory.total_delivered or 0) - float(inventory.total_consumed or 0) - float(inventory.total_defective or 0)
        
        return inventory
