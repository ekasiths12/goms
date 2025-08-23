from extensions import db
from datetime import datetime

class PackingList(db.Model):
    """PackingList model for storing packing list information"""
    __tablename__ = 'packing_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    packing_list_serial = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.Date)
    total_records = db.Column(db.Integer, default=0)
    total_items = db.Column(db.Integer, default=0)
    comments = db.Column(db.Text)
    tax_invoice_number = db.Column(db.String(50))
    
    # Relationships
    packing_list_lines = db.relationship('PackingListLine', backref='packing_list', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PackingList {self.packing_list_serial}>'
    
    def to_dict(self):
        """Convert packing list to dictionary"""
        # Get group bill number from any line that has a billing group
        group_bill_number = None
        for line in self.packing_list_lines:
            if line.stitching_invoice and line.stitching_invoice.billing_group:
                group_bill_number = line.stitching_invoice.billing_group.group_number
                break
        
        return {
            'id': self.id,
            'packing_list_serial': self.packing_list_serial,
            'customer_id': self.customer_id,
            'customer_name': self.customer.short_name if self.customer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'total_records': self.total_records,
            'total_items': self.total_items,
            'comments': self.comments,
            'tax_invoice_number': self.tax_invoice_number,
            'group_bill_number': group_bill_number,
            'line_count': len(self.packing_list_lines)
        }
    
    def calculate_totals(self):
        """Calculate total records and items"""
        self.total_records = len(self.packing_list_lines)
        
        total_items = 0
        for line in self.packing_list_lines:
            size_qty = line.stitching_invoice.get_size_qty()
            total_items += sum(size_qty.values())
        
        self.total_items = total_items
        return self.total_records, self.total_items
    
    @classmethod
    def get_by_serial(cls, serial):
        """Get packing list by serial number"""
        return cls.query.filter_by(packing_list_serial=serial).first()
    
    @classmethod
    def get_by_customer(cls, customer_id):
        """Get all packing lists for a customer"""
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.created_at.desc()).all()

class PackingListLine(db.Model):
    """PackingListLine model for storing packing list line items"""
    __tablename__ = 'packing_list_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    packing_list_id = db.Column(db.Integer, db.ForeignKey('packing_lists.id'), nullable=False)
    stitching_invoice_id = db.Column(db.Integer, db.ForeignKey('stitching_invoices.id'), nullable=False)
    
    def __repr__(self):
        return f'<PackingListLine {self.id}>'
    
    def to_dict(self):
        """Convert packing list line to dictionary"""
        return {
            'id': self.id,
            'packing_list_id': self.packing_list_id,
            'stitching_invoice_id': self.stitching_invoice_id,
            'packing_list_serial': self.packing_list.packing_list_serial if self.packing_list else None,
            'stitching_invoice_number': self.stitching_invoice.stitching_invoice_number if self.stitching_invoice else None,
            'stitched_item': self.stitching_invoice.stitched_item if self.stitching_invoice else None,
            'fabric_name': self.stitching_invoice.item_name if self.stitching_invoice else None,
            'color': self.stitching_invoice.invoice_line.color if self.stitching_invoice and self.stitching_invoice.invoice_line else None,
            'customer_name': self.packing_list.customer.short_name if self.packing_list and self.packing_list.customer else None,
            'tax_invoice_number': self.packing_list.tax_invoice_number if self.packing_list else None,  # MSK Tax #
            'beta_tax_invoice_number': self.stitching_invoice.invoice_line.invoice.tax_invoice_number if self.stitching_invoice and self.stitching_invoice.invoice_line and self.stitching_invoice.invoice_line.invoice else None,  # Beta Tax #
            'group_bill_number': self.stitching_invoice.billing_group.group_number if self.stitching_invoice and self.stitching_invoice.billing_group else None,
            'fabric_invoice_number': self.stitching_invoice.invoice_line.invoice.invoice_number if self.stitching_invoice and self.stitching_invoice.invoice_line and self.stitching_invoice.invoice_line.invoice else None,
            'delivery_note': self.stitching_invoice.invoice_line.delivery_note if self.stitching_invoice and self.stitching_invoice.invoice_line else None,
            'yards_consumed': float(self.stitching_invoice.yard_consumed) if self.stitching_invoice else 0,
            'fabric_unit_price': float(self.stitching_invoice.invoice_line.unit_price) if self.stitching_invoice and self.stitching_invoice.invoice_line else 0,
            'fabric_value': float(self.stitching_invoice.invoice_line.unit_price * self.stitching_invoice.yard_consumed) if self.stitching_invoice and self.stitching_invoice.invoice_line and self.stitching_invoice.yard_consumed else 0,
            'size_qty': self.stitching_invoice.get_size_qty() if self.stitching_invoice else {},
            'size_qty_json': self.stitching_invoice.size_qty_json if self.stitching_invoice else None,
            'total_qty': sum(self.stitching_invoice.get_size_qty().values()) if self.stitching_invoice else 0,
            'price': float(self.stitching_invoice.price) if self.stitching_invoice else 0,
            'total_value': float(self.stitching_invoice.total_value) if self.stitching_invoice else 0,
            'billing_group_id': self.stitching_invoice.billing_group_id if self.stitching_invoice else None,
            'created_at': self.stitching_invoice.created_at.isoformat() if self.stitching_invoice and self.stitching_invoice.created_at else None
        }
