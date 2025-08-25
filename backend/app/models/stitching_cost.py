from extensions import db
from datetime import datetime

class StitchingCost(db.Model):
    """StitchingCost model for memorizing stitching costs by garment and location"""
    __tablename__ = 'stitching_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    garment_name = db.Column(db.String(255), nullable=False)
    stitching_location = db.Column(db.String(255), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint to ensure one cost per garment-location combination
    __table_args__ = (
        db.UniqueConstraint('garment_name', 'stitching_location', name='unique_garment_location_cost'),
    )
    
    def __repr__(self):
        return f'<StitchingCost {self.garment_name} - {self.stitching_location}: {self.cost}>'
    
    def to_dict(self):
        """Convert stitching cost to dictionary"""
        return {
            'id': self.id,
            'garment_name': self.garment_name,
            'stitching_location': self.stitching_location,
            'cost': float(self.cost) if self.cost else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_garment_and_location(cls, garment_name, stitching_location):
        """Get memorized cost for a specific garment and location combination"""
        return cls.query.filter_by(
            garment_name=garment_name,
            stitching_location=stitching_location
        ).first()
    
    @classmethod
    def get_all_costs(cls):
        """Get all memorized costs ordered by garment name and location"""
        return cls.query.order_by(cls.garment_name, cls.stitching_location).all()
    
    @classmethod
    def create_or_update_cost(cls, garment_name, stitching_location, cost):
        """Create or update cost for a garment-location combination"""
        existing_cost = cls.get_by_garment_and_location(garment_name, stitching_location)
        
        if existing_cost:
            existing_cost.cost = cost
            existing_cost.updated_at = datetime.utcnow()
            db.session.flush()
            return existing_cost
        else:
            new_cost = cls(
                garment_name=garment_name,
                stitching_location=stitching_location,
                cost=cost
            )
            db.session.add(new_cost)
            db.session.flush()
            return new_cost
