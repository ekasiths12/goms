# Backend Code Refactoring and Optimization Suggestions

## Executive Summary

This document provides comprehensive suggestions for refactoring and optimizing the GOMS (Garment Management System) **backend** codebase. The analysis identifies duplicated code patterns, optimization opportunities, and architectural improvements.

---

## 1. CRITICAL: Duplicated Code Patterns

### 1.1 Database Session Management
**Issue**: Inconsistent database session handling across routes
- Some routes use `db.session.rollback()` in except blocks
- Some use nested try-except blocks
- Some don't handle rollbacks at all

**Location**: All route files (`invoices.py`, `stitching.py`, `packing_lists.py`, etc.)

**Solution**: Create a decorator for database transaction management
```python
# backend/app/utils/db_decorators.py
from functools import wraps
from extensions import db

def db_transaction(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            raise e
    return decorated_function
```

### 1.2 Error Response Formatting
**Issue**: Inconsistent error response formats
- Some return `{'error': str(e)}`
- Some return `jsonify({'error': str(e)})`
- Some return tuples `({'error': str(e)}, 500)`
- Some use `'success': False` pattern

**Location**: All route files

**Solution**: Create a standardized response utility
```python
# backend/app/utils/response_utils.py
from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return jsonify(response), status_code

def error_response(error, status_code=500):
    return jsonify({'success': False, 'error': str(error)}), status_code
```

### 1.3 Date Parsing Logic
**Issue**: Date parsing code duplicated across multiple files
- `DD/MM/YY` to `YYYY-MM-DD` conversion appears in `invoices.py` (lines 85-109)
- `format_ddmmyy` function duplicated in `packing_lists.py` (line 348) and `group_bills.py` (line 1295)
- Date validation logic scattered

**Location**: 
- `backend/app/routes/invoices.py` (lines 85-109)
- `backend/app/routes/packing_lists.py` (line 348)
- `backend/app/routes/group_bills.py` (line 1295)

**Solution**: Create a centralized date utility
```python
# backend/app/utils/date_utils.py
from datetime import datetime

def parse_ddmmyy(date_string):
    """Parse DD/MM/YY format to datetime object"""
    if not date_string or len(date_string) != 8 or date_string.count('/') != 2:
        return None
    try:
        day, month, year = date_string.split('/')
        if len(year) == 2:
            year = '20' + year if int(year) < 50 else '19' + year
        return datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", '%Y-%m-%d')
    except (ValueError, IndexError):
        return None

def format_ddmmyy(date_obj):
    """Format datetime/date object to DD/MM/YY string"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S').date()
            except ValueError:
                return str(date_obj)
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%d/%m/%y')
    return str(date_obj)
```

### 1.4 Query Filter Building
**Issue**: Similar filter building patterns repeated across routes
- Customer filter: `Customer.short_name.ilike(f'%{customer_filter}%')`
- Date range filters duplicated
- Invoice number filters duplicated

**Location**: 
- `invoices.py` (lines 72-109)
- `stitching.py` (lines 39-59)
- `packing_lists.py` (lines 36-79)
- `group_bills.py` (lines 29-44)

**Solution**: Create query builder utilities
```python
# backend/app/utils/query_utils.py
from sqlalchemy import and_, or_

class QueryFilterBuilder:
    @staticmethod
    def add_text_filter(query, model, field_name, filter_value):
        if filter_value:
            return query.filter(getattr(model, field_name).ilike(f'%{filter_value}%'))
        return query
    
    @staticmethod
    def add_date_range_filter(query, model, field_name, date_from, date_to):
        if date_from:
            date_from_obj = parse_ddmmyy(date_from) or parse_iso_date(date_from)
            if date_from_obj:
                query = query.filter(getattr(model, field_name) >= date_from_obj)
        if date_to:
            date_to_obj = parse_ddmmyy(date_to) or parse_iso_date(date_to)
            if date_to_obj:
                query = query.filter(getattr(model, field_name) <= date_to_obj)
        return query
```

### 1.5 PDF Generation Code Duplication
**Issue**: Massive duplication in PDF generation
- `generate_packing_list_pdf_old` (line 363) - OLD VERSION (BACKUP) - should be removed
- Multiple cost breakdown functions: `add_cost_breakdown_to_pdf`, `add_cost_breakdown_modern`, `add_cost_breakdown_apple`, `add_cost_breakdown_apple_right`, `add_cost_breakdown_minimal_horizontal`
- Similar PDF header/footer code in `packing_lists.py` and `group_bills.py`

**Location**: 
- `backend/app/routes/packing_lists.py` (lines 363-1382)
- `backend/app/routes/group_bills.py` (lines 234-1293)

**Solution**: Extract PDF generation to a service layer
```python
# backend/app/services/pdf_service.py
class PDFService:
    def __init__(self):
        self.pdf = None
    
    def create_pdf(self, orientation='P', format='A4'):
        from fpdf import FPDF
        self.pdf = FPDF(orientation, 'mm', format)
        self.pdf.add_page()
        return self.pdf
    
    def add_header(self, company_name, subtitle, document_title):
        # Centralized header logic
        pass
    
    def add_table(self, headers, data, col_widths):
        # Centralized table logic
        pass
```

### 1.6 Cost Calculation Logic
**Issue**: Garment cost calculation duplicated
- `calculate_garment_cost_per_piece` in `packing_lists.py` (line 937)
- Similar logic in `get_packing_lists` (lines 123-152)
- Similar logic in cost breakdown functions

**Solution**: Extract to a service
```python
# backend/app/services/cost_calculation_service.py
class CostCalculationService:
    @staticmethod
    def calculate_garment_cost(stitching_record, include_vat=True):
        # Centralized cost calculation
        pass
```

---

## 2. Database Query Optimizations

### 2.1 N+1 Query Problems
**Issue**: Multiple queries in loops
- `get_invoices` loads commission_sales separately (line 68)
- `get_stitching` loads images separately (line 37)
- `get_packing_lists` loads related data in loops

**Location**: 
- `invoices.py` (line 68)
- `stitching.py` (line 37)
- `packing_lists.py` (lines 106-157)

**Solution**: Use eager loading consistently
```python
# Use joinedload for relationships
query = query.options(
    db.joinedload(InvoiceLine.commission_sales),
    db.joinedload(InvoiceLine.invoice).joinedload(Invoice.customer)
)
```

### 2.2 Raw SQL in Routes
**Issue**: Raw SQL queries mixed with ORM queries
- `get_available_fabrics` uses raw SQL (line 691)
- `get_invoices` uses ORM but could be optimized

**Location**: 
- `stitching.py` (line 691)
- `dashboard.py` (multiple locations)

**Solution**: Move complex queries to model methods or query builders

### 2.3 Missing Indexes
**Issue**: No explicit index definitions visible
- Frequent filters on `invoice_number`, `customer_id`, `created_at`
- No composite indexes for common query patterns

**Solution**: Add database indexes
```python
# In models
class Invoice(db.Model):
    __table_args__ = (
        db.Index('idx_invoice_customer_date', 'customer_id', 'invoice_date'),
        db.Index('idx_invoice_number', 'invoice_number'),
    )
```

---

## 3. Code Organization Issues

### 3.1 Route Files Too Large
**Issue**: Some route files are extremely large
- `packing_lists.py`: 1383 lines
- `group_bills.py`: 1457 lines
- `dashboard.py`: 2172 lines (exceeds token limit)

**Solution**: Split into smaller modules
```
backend/app/routes/
  packing_lists/
    __init__.py
    routes.py
    pdf_generator.py
    cost_calculator.py
```

### 3.2 Business Logic in Routes
**Issue**: Business logic mixed with route handlers
- PDF generation logic in routes
- Cost calculation in routes
- Data transformation in routes

**Solution**: Move to service layer
```
backend/app/services/
  pdf_service.py
  cost_calculation_service.py
  invoice_service.py
  stitching_service.py
```

### 3.3 Model Methods Missing
**Issue**: Data transformation logic in routes instead of models
- `to_dict()` methods exist but some transformations happen in routes
- Serialization logic scattered

**Solution**: Enhance model methods
```python
# In models
class StitchingInvoice(db.Model):
    def to_dict(self, include_related=True):
        data = {
            'id': self.id,
            'stitching_invoice_number': self.stitching_invoice_number,
            # ... basic fields
        }
        if include_related:
            data['garment_fabrics'] = [f.to_dict() for f in self.garment_fabrics]
            data['lining_fabrics'] = [l.to_dict() for l in self.lining_fabrics]
        return data
```

---

## 4. Configuration and Constants

### 4.1 Magic Numbers and Strings
**Issue**: Hardcoded values throughout code
- VAT rate: `1.07` or `0.07` scattered
- Size names: `["S", "M", "L", "XL", "XXL", "XXXL"]` repeated
- Color codes, page dimensions, etc.

**Location**: Multiple files

**Solution**: Create constants file
```python
# backend/app/utils/constants.py
VAT_RATE = 0.07
SIZES = ["S", "M", "L", "XL", "XXL", "XXXL"]
PAGE_WIDTH_A4_PORTRAIT = 210
PAGE_HEIGHT_A4_PORTRAIT = 297
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
```

### 4.2 Configuration Duplication
**Issue**: Similar configuration in multiple places
- CORS origins hardcoded in `main.py` (line 46)
- Upload settings in `config.py` and `images.py`

**Solution**: Centralize in config
```python
# config/config.py
class Config:
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # ... from environment or config
    ]
```

---

## 5. Error Handling Improvements

### 5.1 Inconsistent Exception Handling
**Issue**: Different exception handling patterns
- Some catch all `Exception`
- Some catch specific exceptions
- Some don't catch at all

**Solution**: Create custom exceptions
```python
# backend/app/utils/exceptions.py
class GOMSException(Exception):
    pass

class ValidationError(GOMSException):
    pass

class NotFoundError(GOMSException):
    pass

class DatabaseError(GOMSException):
    pass
```

### 5.2 Error Logging
**Issue**: Print statements instead of proper logging
- `print(f"DEBUG: ...")` throughout code
- No structured logging

**Solution**: Use Python logging
```python
# backend/app/utils/logger.py
import logging

logger = logging.getLogger('goms')
logger.setLevel(logging.INFO)

# In routes
logger.error(f"Error in get_invoices: {str(e)}", exc_info=True)
```

---

## 6. Frontend Route Duplication

### 6.1 Duplicate Route Handlers
**Issue**: Multiple routes serving same file
- `/fabric-invoices.html` and `/fabric-invoices` (lines 210-225)
- `/stitching-records.html` and `/stitching-records` (lines 227-233)
- Pattern repeated for all pages

**Location**: `backend/main.py` (lines 198-265)

**Solution**: Use Flask's `send_from_directory` with route parameter
```python
@app.route('/<path:filename>')
def serve_frontend(filename):
    # Remove .html extension if present
    if filename.endswith('.html'):
        filename = filename[:-5]
    elif not filename.endswith('.html'):
        filename = filename + '.html'
    return send_from_directory(app.static_folder, filename)
```

---

## 7. Import Organization

### 7.1 Inconsistent Imports
**Issue**: Different import patterns
- Some use `from extensions import db`
- Some use `from main import db` (customers.py line 4)
- Some import from models directly

**Location**: 
- `customers.py` (line 4): `from main import db` (WRONG - should use extensions)
- `files.py` (line 5): `from main import db` (WRONG)

**Solution**: Standardize all imports
```python
# Always use
from extensions import db
```

---

## 8. Performance Optimizations

### 8.1 Unnecessary Database Queries
**Issue**: Queries that could be combined
- Multiple separate queries in `get_packing_lists`
- Loading related data in loops

**Solution**: Use eager loading and batch operations

### 8.2 PDF Generation Caching
**Issue**: PDFs regenerated on every request
- No caching mechanism
- Same PDF generated multiple times

**Solution**: Implement caching
```python
# Cache generated PDFs
@cache.memoize(timeout=3600)
def generate_packing_list_pdf(packing_list_id):
    # ... generation logic
```

### 8.3 Image Loading Optimization
**Issue**: Images loaded individually
- `image_map` built by querying each image separately

**Solution**: Batch load images
```python
images = Image.query.filter(Image.id.in_(image_ids)).all()
image_map = {img.id: img.get_image_path_for_pdf() for img in images}
```

---

## 9. Code Quality Issues

### 9.1 Debug Code in Production
**Issue**: Debug print statements throughout
- `print(f"DEBUG: ...")` statements
- Commented out code
- Old backup functions (`generate_packing_list_pdf_old`)

**Location**: Multiple files

**Solution**: Remove debug code, use logging

### 9.2 Long Functions
**Issue**: Functions exceeding 100 lines
- `generate_packing_list_pdf`: 362 lines
- `generate_stitching_fee_pdf`: 624 lines
- `get_dashboard_summary`: 341 lines

**Solution**: Break into smaller functions

### 9.3 Code Comments
**Issue**: Inconsistent commenting
- Some functions well-documented
- Some have no docstrings
- Mixed comment styles

**Solution**: Standardize docstrings
```python
def function_name(param1, param2):
    """
    Brief description.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When this happens
    """
```

---

## 10. Security Considerations

### 10.1 SQL Injection Risks
**Issue**: Some raw SQL queries
- String formatting in queries (though using parameterized queries in most places)

**Solution**: Always use parameterized queries

### 10.2 File Upload Security
**Issue**: Basic file validation
- `allowed_file` checks extension only
- No content-type validation
- No virus scanning

**Solution**: Enhance validation
```python
def validate_image(file):
    # Check extension
    # Check MIME type
    # Validate file content (PIL)
    # Check file size
    pass
```

---

## Priority Recommendations

### High Priority (Do First)
1. Fix database import inconsistencies (`from main import db` → `from extensions import db`)
2. Create response utility for consistent error handling
3. Extract date parsing to utility module
4. Remove duplicate `format_ddmmyy` functions
5. Remove old/unused code (`generate_packing_list_pdf_old`)
6. Create database transaction decorator

### Medium Priority
1. Extract PDF generation to service layer
2. Create query builder utilities
3. Move business logic to services
4. Add proper logging
5. Extract constants to constants file

### Low Priority (Nice to Have)
1. Split large route files
2. Add comprehensive docstrings
3. Implement PDF caching
4. Add database indexes
5. Enhance file upload security

---

## Implementation Order

1. **Week 1**: Fix critical issues (imports, response utils, date utils)
2. **Week 2**: Extract utilities (query builders, constants)
3. **Week 3**: Service layer extraction (PDF, cost calculation)
4. **Week 4**: Code organization (split files, add logging)
5. **Week 5**: Performance optimizations (caching, indexes)

---

## Estimated Impact

- **Code Reduction**: ~30-40% reduction in duplicated code
- **Maintainability**: Significantly improved with centralized utilities
- **Performance**: 20-30% improvement with query optimizations
- **Bug Reduction**: Fewer bugs from inconsistent error handling

---

## Notes

- All refactoring should be done incrementally
- Maintain backward compatibility during transition
- Add tests for new utility functions
- Document all new service layers
- **Backend refactoring should be done module-by-module to avoid breaking changes**
