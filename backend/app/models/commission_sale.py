from extensions import db
from datetime import datetime
from decimal import Decimal

class CommissionSale(db.Model):
    """CommissionSale model for tracking individual commission sales"""
    __tablename__ = 'commission_sales'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_line_id = db.Column(db.Integer, db.ForeignKey('invoice_lines.id'), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    yards_sold = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 4), default=0.051)  # 5.1% default
    commission_amount = db.Column(db.Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    customer_name = db.Column(db.String(255))
    item_name = db.Column(db.String(255))
    color = db.Column(db.String(100))
    delivered_location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    invoice_line = db.relationship('InvoiceLine', backref='commission_sales', lazy=True)
    
    def __repr__(self):
        return f'<CommissionSale {self.serial_number} - {self.yards_sold} yards>'
    
    def to_dict(self):
        """Convert commission sale to dictionary"""
        return {
            'id': self.id,
            'invoice_line_id': self.invoice_line_id,
            'serial_number': self.serial_number,
            'yards_sold': float(self.yards_sold) if self.yards_sold else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0,
            'commission_amount': float(self.commission_amount) if self.commission_amount else 0,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'customer_name': self.customer_name,
            'item_name': self.item_name,
            'color': self.color,
            'delivered_location': self.delivered_location,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'invoice_number': self.invoice_line.invoice.invoice_number if self.invoice_line and self.invoice_line.invoice else None
        }
    
    @classmethod
    def generate_serial_number(cls):
        """Generate a unique serial number for commission sale"""
        from app.models.serial_counter import SerialCounter
        
        counter = SerialCounter.get_or_create('CS')
        serial_number = f"CS{datetime.now().strftime('%y%m%d')}{counter.last_value + 1:04d}"
        counter.increment()
        return serial_number
    
    @classmethod
    def create_commission_sale(cls, invoice_line_id, yards_sold, sale_date, unit_price=None):
        """Create a new commission sale"""
        from app.models.invoice import InvoiceLine
        
        # Get the invoice line
        invoice_line = InvoiceLine.query.get(invoice_line_id)
        if not invoice_line:
            raise ValueError("Invoice line not found")
        
        # Calculate pending yards (excluding existing commission sales)
        existing_commission_yards = sum(cs.yards_sold for cs in invoice_line.commission_sales)
        pending_yards = (invoice_line.yards_sent or 0) - (invoice_line.yards_consumed or 0) - existing_commission_yards
        
        if yards_sold > pending_yards:
            raise ValueError(f"Cannot sell {yards_sold} yards, only {pending_yards} yards available")
        
        # Use invoice line unit price if not provided
        if unit_price is None:
            unit_price = invoice_line.unit_price or 0
        
        # Calculate commission amount
        commission_amount = yards_sold * unit_price * Decimal('0.051')
        
        # Create commission sale
        commission_sale = cls(
            invoice_line_id=invoice_line_id,
            serial_number=cls.generate_serial_number(),
            yards_sold=yards_sold,
            unit_price=unit_price,
            commission_amount=commission_amount,
            sale_date=sale_date,
            customer_name=invoice_line.invoice.customer.short_name if invoice_line.invoice and invoice_line.invoice.customer else None,
            item_name=invoice_line.item_name,
            color=invoice_line.color,
            delivered_location=invoice_line.delivered_location
        )
        
        db.session.add(commission_sale)
        return commission_sale
