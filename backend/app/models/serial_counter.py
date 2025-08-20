from app import db

class SerialCounter(db.Model):
    """SerialCounter model for managing serial number sequences"""
    __tablename__ = 'serial_counters'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_type = db.Column(db.String(10), unique=True, nullable=False)  # ST, GB, PL, GBN
    last_value = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<SerialCounter {self.serial_type}: {self.last_value}>'
    
    def to_dict(self):
        """Convert serial counter to dictionary"""
        return {
            'id': self.id,
            'serial_type': self.serial_type,
            'last_value': self.last_value
        }
    
    @classmethod
    def get_or_create(cls, serial_type):
        """Get or create a serial counter for the given type"""
        counter = cls.query.filter_by(serial_type=serial_type).first()
        if not counter:
            counter = cls(serial_type=serial_type, last_value=0)
            db.session.add(counter)
            db.session.commit()
        return counter
    
    def increment(self):
        """Increment the counter and return the new value"""
        self.last_value += 1
        db.session.commit()
        return self.last_value
