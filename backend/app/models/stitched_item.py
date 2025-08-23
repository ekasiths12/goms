from extensions import db
from datetime import datetime

class StitchedItem(db.Model):
    __tablename__ = 'stitched_items'
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
    def get_all_items(cls):
        return cls.query.order_by(cls.name).all()
    
    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def create_item(cls, name):
        item = cls(name=name)
        db.session.add(item)
        db.session.flush()
        return item
    
    @classmethod
    def delete_item(cls, item_id):
        item = cls.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.flush()
            return True
        return False
