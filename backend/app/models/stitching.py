from extensions import db
from datetime import datetime
import json

class StitchingInvoice(db.Model):
    """StitchingInvoice model for storing stitching records"""
    __tablename__ = 'stitching_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    stitching_invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    yard_consumed = db.Column(db.Numeric(10, 2), default=0)
    stitched_item = db.Column(db.String(255), nullable=False)
    size_qty_json = db.Column(db.Text)  # JSON string for size quantities
    price = db.Column(db.Numeric(10, 2), default=0)
    total_value = db.Column(db.Numeric(12, 2), default=0)
    add_vat = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_line_id = db.Column(db.Integer, db.ForeignKey('invoice_lines.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'))
    billing_group_id = db.Column(db.Integer, db.ForeignKey('stitching_invoice_groups.id'))
    total_lining_cost = db.Column(db.Numeric(12, 2), default=0)
    total_fabric_cost = db.Column(db.Numeric(12, 2), default=0)
    
    # Relationships
    garment_fabrics = db.relationship('GarmentFabric', backref='stitching_invoice', lazy=True, cascade='all, delete-orphan')
    lining_fabrics = db.relationship('LiningFabric', backref='stitching_invoice', lazy=True, cascade='all, delete-orphan')
    packing_list_lines = db.relationship('PackingListLine', backref='stitching_invoice', lazy=True)
    group_lines = db.relationship('StitchingInvoiceGroupLine', backref='stitching_invoice', lazy=True)
    
    def __repr__(self):
        return f'<StitchingInvoice {self.stitching_invoice_number}>'
    
    def to_dict(self):
        """Convert stitching invoice to dictionary"""
        # Get image information if available (using existing relationship)
        image_data = None
        if self.image_id and hasattr(self, 'image') and self.image:
            image_data = {
                'id': self.image.id,
                'file_path': self.image.file_path,
                'image_url': self.image.get_image_url(),
                'filename': self.image.file_path.split('/')[-1] if self.image.file_path else None
            }
        
        return {
            'id': self.id,
            'stitching_invoice_number': self.stitching_invoice_number,
            'item_name': self.item_name,
            'yard_consumed': float(self.yard_consumed) if self.yard_consumed else 0,
            'stitched_item': self.stitched_item,
            'size_qty': self.get_size_qty(),
            'size_qty_json': self.size_qty_json,  # Add the raw JSON string
            'price': float(self.price) if self.price else 0,
            'total_value': float(self.total_value) if self.total_value else 0,
            'add_vat': self.add_vat,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'invoice_line_id': self.invoice_line_id,
            'image_id': self.image_id,
            'image': image_data,  # Add image information
            'billing_group_id': self.billing_group_id,
            'total_lining_cost': float(self.total_lining_cost) if self.total_lining_cost else 0,
            'total_fabric_cost': float(self.total_fabric_cost) if self.total_fabric_cost else 0,
            'fabric_name': self.invoice_line.item_name if self.invoice_line else None,
            'color': self.invoice_line.color if self.invoice_line else None,
            'customer_name': self.invoice_line.invoice.customer.short_name if self.invoice_line and self.invoice_line.invoice else None,
            'tax_invoice_number': self.invoice_line.invoice.tax_invoice_number if self.invoice_line and self.invoice_line.invoice else None,
            'fabric_invoice_number': self.invoice_line.invoice.invoice_number if self.invoice_line and self.invoice_line.invoice else None,
            'delivery_note': self.invoice_line.delivery_note if self.invoice_line else None,
            'fabric_unit_price': float(self.invoice_line.unit_price) if self.invoice_line else 0,
            'fabric_value': float(self.invoice_line.unit_price * self.yard_consumed) if self.invoice_line and self.yard_consumed else 0
        }
    
    def get_size_qty(self):
        """Get size quantities as dictionary"""
        if self.size_qty_json:
            try:
                return json.loads(self.size_qty_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_size_qty(self, size_qty_dict):
        """Set size quantities from dictionary"""
        self.size_qty_json = json.dumps(size_qty_dict)
    
    def calculate_total(self):
        """Calculate total value including VAT if applicable"""
        total_qty = sum(self.get_size_qty().values())
        base_total = self.price * total_qty
        
        if self.add_vat:
            self.total_value = base_total * 1.07  # Add 7% VAT
        else:
            self.total_value = base_total
        
        return self.total_value
    
    @classmethod
    def get_by_serial_number(cls, serial_number):
        """Get stitching invoice by serial number"""
        return cls.query.filter_by(stitching_invoice_number=serial_number).first()
    
    @classmethod
    def get_unbilled(cls):
        """Get all unbilled stitching invoices"""
        return cls.query.filter_by(billing_group_id=None).order_by(cls.created_at.desc()).all()

class GarmentFabric(db.Model):
    """GarmentFabric model for storing multi-fabric information"""
    __tablename__ = 'garment_fabrics'
    
    id = db.Column(db.Integer, primary_key=True)
    stitching_invoice_id = db.Column(db.Integer, db.ForeignKey('stitching_invoices.id'), nullable=False)
    fabric_invoice_line_id = db.Column(db.Integer, db.ForeignKey('invoice_lines.id'), nullable=False)
    consumption_yards = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    total_fabric_cost = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<GarmentFabric {self.id}>'
    
    def to_dict(self):
        """Convert garment fabric to dictionary"""
        pending_yards = 0
        if self.invoice_line:
            pending_yards = (self.invoice_line.yards_sent or 0) - (self.invoice_line.yards_consumed or 0)
        
        return {
            'id': self.id,
            'stitching_invoice_id': self.stitching_invoice_id,
            'fabric_invoice_line_id': self.fabric_invoice_line_id,
            'consumption_yards': float(self.consumption_yards) if self.consumption_yards else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'total_fabric_cost': float(self.total_fabric_cost) if self.total_fabric_cost else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'fabric_name': self.invoice_line.item_name if self.invoice_line else None,
            'color': self.invoice_line.color if self.invoice_line else None,
            'invoice_number': self.invoice_line.invoice.invoice_number if self.invoice_line and self.invoice_line.invoice else None,
            'pending_yards': pending_yards
        }
    
    def calculate_total_cost(self):
        """Calculate total fabric cost"""
        self.total_fabric_cost = self.consumption_yards * self.unit_price
        return self.total_fabric_cost

class LiningFabric(db.Model):
    """LiningFabric model for storing lining fabric information"""
    __tablename__ = 'lining_fabrics'
    
    id = db.Column(db.Integer, primary_key=True)
    stitching_invoice_id = db.Column(db.Integer, db.ForeignKey('stitching_invoices.id'), nullable=False)
    lining_name = db.Column(db.String(255), nullable=False)
    consumption_yards = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    total_cost = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LiningFabric {self.lining_name}>'
    
    def to_dict(self):
        """Convert lining fabric to dictionary"""
        return {
            'id': self.id,
            'stitching_invoice_id': self.stitching_invoice_id,
            'lining_name': self.lining_name,
            'consumption_yards': float(self.consumption_yards) if self.consumption_yards else 0,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def calculate_total_cost(self):
        """Calculate total cost"""
        self.total_cost = self.consumption_yards * self.unit_price
        return self.total_cost
