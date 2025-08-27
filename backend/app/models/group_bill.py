from extensions import db
from datetime import datetime

class StitchingInvoiceGroup(db.Model):
    """StitchingInvoiceGroup model for storing group bill information"""
    __tablename__ = 'stitching_invoice_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    group_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_date = db.Column(db.Date)
    stitching_comments = db.Column(db.Text)
    fabric_comments = db.Column(db.Text)
    
    # Relationships
    group_lines = db.relationship('StitchingInvoiceGroupLine', backref='group', lazy=True, cascade='all, delete-orphan')
    stitching_invoices = db.relationship('StitchingInvoice', backref='billing_group', lazy=True)
    
    def __repr__(self):
        return f'<StitchingInvoiceGroup {self.group_number}>'
    
    def to_dict(self):
        """Convert group bill to dictionary"""
        return {
            'id': self.id,
            'group_number': self.group_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.short_name if self.customer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'stitching_comments': self.stitching_comments,
            'fabric_comments': self.fabric_comments,
            'line_count': len(self.group_lines)
        }
    
    def calculate_totals(self):
        """Calculate totals for the group - FIXED: Now includes secondary fabrics"""
        total_stitching_value = 0
        total_fabric_value = 0
        total_items = 0
        
        for line in self.group_lines:
            stitching_invoice = line.stitching_invoice
            if stitching_invoice:
                total_stitching_value += float(stitching_invoice.total_value or 0)
                
                # Calculate fabric value - FIXED: Include both main and secondary fabrics
                fabric_value = 0
                
                # Main fabric value
                if stitching_invoice.invoice_line and stitching_invoice.yard_consumed:
                    fabric_value += float(stitching_invoice.invoice_line.unit_price * stitching_invoice.yard_consumed)
                
                # Secondary fabrics value from garment_fabrics table
                for garment_fabric in stitching_invoice.garment_fabrics:
                    fabric_value += float(garment_fabric.total_fabric_cost or 0)
                
                total_fabric_value += fabric_value
                
                # Calculate total items
                size_qty = stitching_invoice.get_size_qty()
                total_items += sum(size_qty.values())
        
        return {
            'total_stitching_value': total_stitching_value,
            'total_fabric_value': total_fabric_value,
            'total_items': total_items
        }
    
    @classmethod
    def get_by_group_number(cls, group_number):
        """Get group bill by group number"""
        return cls.query.filter_by(group_number=group_number).first()
    
    @classmethod
    def get_by_customer(cls, customer_id):
        """Get all group bills for a customer"""
        return cls.query.filter_by(customer_id=customer_id).order_by(cls.created_at.desc()).all()

class StitchingInvoiceGroupLine(db.Model):
    """StitchingInvoiceGroupLine model for storing group bill line items"""
    __tablename__ = 'stitching_invoice_group_lines'
    
    group_id = db.Column(db.Integer, db.ForeignKey('stitching_invoice_groups.id'), primary_key=True)
    stitching_invoice_id = db.Column(db.Integer, db.ForeignKey('stitching_invoices.id'), primary_key=True)
    
    def __repr__(self):
        return f'<StitchingInvoiceGroupLine {self.id}>'
    
    def to_dict(self):
        """Convert group bill line to dictionary - FIXED: Now includes secondary fabrics"""
        fabric_value = 0
        
        # Main fabric value
        if self.stitching_invoice and self.stitching_invoice.invoice_line and self.stitching_invoice.yard_consumed:
            fabric_value += float(self.stitching_invoice.invoice_line.unit_price * self.stitching_invoice.yard_consumed)
        
        # Secondary fabrics value
        if self.stitching_invoice:
            for garment_fabric in self.stitching_invoice.garment_fabrics:
                fabric_value += float(garment_fabric.total_fabric_cost or 0)
        
        return {
            'group_id': self.group_id,
            'stitching_invoice_id': self.stitching_invoice_id,
            'stitching_invoice_number': self.stitching_invoice.stitching_invoice_number if self.stitching_invoice else None,
            'item_name': self.stitching_invoice.item_name if self.stitching_invoice else None,
            'stitched_item': self.stitching_invoice.stitched_item if self.stitching_invoice else None,
            'yard_consumed': float(self.stitching_invoice.yard_consumed) if self.stitching_invoice else 0,
            'fabric_unit_price': float(self.stitching_invoice.invoice_line.unit_price) if self.stitching_invoice and self.stitching_invoice.invoice_line else 0,
            'fabric_value': fabric_value,  # FIXED: Now includes secondary fabrics
            'size_qty': self.stitching_invoice.get_size_qty() if self.stitching_invoice else {},
            'total_qty': sum(self.stitching_invoice.get_size_qty().values()) if self.stitching_invoice else 0,
            'price': float(self.stitching_invoice.price) if self.stitching_invoice else 0,
            'total_value': float(self.stitching_invoice.total_value) if self.stitching_invoice else 0,
            'created_at': self.stitching_invoice.created_at.isoformat() if self.stitching_invoice and self.stitching_invoice.created_at else None
        }
