from extensions import db
from datetime import datetime

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
    
    @classmethod
    def get_next_counter(cls, serial_type):
        """Get the next counter value for a serial type"""
        counter = cls.get_or_create(serial_type)
        return counter.increment()
    
    @classmethod
    def generate_serial_number(cls, serial_type):
        """Generate a serial number for the given type"""
        now = datetime.now()
        
        if serial_type == "ST":
            # ST/MMYY/XXX format
            mm_yy = now.strftime('%m%y')
            pattern = f"ST/{mm_yy}/%"
            format_string = f"ST/{mm_yy}/{{:03d}}"
            return cls._get_next_number("stitching_invoices", "stitching_invoice_number", pattern, format_string)
        
        elif serial_type == "GB":
            # GB/MMYY/XXX format
            mm_yy = now.strftime('%m%y')
            pattern = f"GB/{mm_yy}/%"
            format_string = f"GB/{mm_yy}/{{:03d}}"
            return cls._get_next_number("stitching_invoice_groups", "group_number", pattern, format_string)
        
        elif serial_type == "PL":
            # PLYYMMDDXX format
            date_str = now.strftime('%y%m%d')
            pattern = f"PL{date_str}%"
            format_string = f"PL{date_str}{{:02d}}"
            return cls._get_next_number("packing_lists", "packing_list_serial", pattern, format_string)
        
        elif serial_type == "GBN":
            # GBNYYMMDDXX format
            date_str = now.strftime('%y%m%d')
            pattern = f"GBN{date_str}%"
            format_string = f"GBN{date_str}{{:02d}}"
            return cls._get_next_number("stitching_invoice_groups", "group_number", pattern, format_string)
        
        else:
            raise ValueError(f"Unknown serial type: {serial_type}")
    
    @classmethod
    def _get_next_number(cls, table_name, column_name, pattern, format_string):
        """Find the next available number for a given pattern"""
        # Get all existing serials for this pattern
        if table_name == "stitching_invoices":
            from app.models.stitching import StitchingInvoice
            existing_serials = db.session.query(getattr(StitchingInvoice, column_name)).filter(
                getattr(StitchingInvoice, column_name).like(pattern)
            ).all()
        elif table_name == "stitching_invoice_groups":
            from app.models.group_bill import StitchingInvoiceGroup
            existing_serials = db.session.query(getattr(StitchingInvoiceGroup, column_name)).filter(
                getattr(StitchingInvoiceGroup, column_name).like(pattern)
            ).all()
        elif table_name == "packing_lists":
            from app.models.packing_list import PackingList
            existing_serials = db.session.query(getattr(PackingList, column_name)).filter(
                getattr(PackingList, column_name).like(pattern)
            ).all()
        else:
            raise ValueError(f"Unknown table: {table_name}")
        
        # Extract numeric parts
        numbers = []
        for (serial,) in existing_serials:
            if serial:
                try:
                    # Extract the numeric part based on the pattern
                    if pattern.startswith("ST/") or pattern.startswith("GB/"):
                        # ST/MMYY/XXX or GB/MMYY/XXX format
                        numeric_part = int(serial.split('/')[-1])
                    else:
                        # PLYYMMDDXX or GBNYYMMDDXX format
                        numeric_part = int(serial[-2:])
                    numbers.append(numeric_part)
                except (ValueError, IndexError):
                    continue
        
        # Find next number (start from 1 if no existing numbers)
        next_number = 1 if not numbers else max(numbers) + 1
        
        return format_string.format(next_number)
