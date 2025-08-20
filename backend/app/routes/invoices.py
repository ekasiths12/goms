from flask import Blueprint, request, jsonify
from app.models.invoice import Invoice, InvoiceLine
from app.models.customer import Customer
from main import db
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from datetime import datetime
import traceback

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/', methods=['GET'])
def get_invoices():
    """Get all invoices with line items and customer information"""
    try:
        print("DEBUG: get_invoices called")
        # Get query parameters for filtering
        customer_filter = request.args.get('customer')
        invoice_number_filter = request.args.get('invoice_number')
        tax_invoice_filter = request.args.get('tax_invoice')
        item_code_filter = request.args.get('item_code')
        dn_filter = request.args.get('dn')
        location_filter = request.args.get('location')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        show_consumed = request.args.get('show_consumed', 'false').lower() == 'true'

        print(f"DEBUG: Filters - customer: {customer_filter}, show_consumed: {show_consumed}")

        # Build query
        query = db.session.query(InvoiceLine).join(Invoice).join(Customer)
        
        # Apply filters
        if customer_filter:
            query = query.filter(Customer.short_name.ilike(f'%{customer_filter}%'))
        if invoice_number_filter:
            query = query.filter(Invoice.invoice_number.ilike(f'%{invoice_number_filter}%'))
        if tax_invoice_filter:
            query = query.filter(Invoice.tax_invoice_number.ilike(f'%{tax_invoice_filter}%'))
        if item_code_filter:
            query = query.filter(InvoiceLine.item_name.ilike(f'%{item_code_filter}%'))
        if dn_filter:
            query = query.filter(InvoiceLine.delivery_note.ilike(f'%{dn_filter}%'))
        if location_filter:
            query = query.filter(InvoiceLine.delivered_location.ilike(f'%{location_filter}%'))
        if date_from:
            try:
                # Convert DD/MM/YY to YYYY-MM-DD (like old Qt app)
                if len(date_from) == 8 and date_from.count('/') == 2:
                    day, month, year = date_from.split('/')
                    # Convert 2-digit year to 4-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_from_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    date_from_obj = datetime.strptime(date_from_iso, '%Y-%m-%d')
                    query = query.filter(Invoice.invoice_date >= date_from_obj)
            except (ValueError, IndexError):
                pass
        if date_to:
            try:
                # Convert DD/MM/YY to YYYY-MM-DD (like old Qt app)
                if len(date_to) == 8 and date_to.count('/') == 2:
                    day, month, year = date_to.split('/')
                    # Convert 2-digit year to 4-digit year
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    date_to_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    date_to_obj = datetime.strptime(date_to_iso, '%Y-%m-%d')
                    query = query.filter(Invoice.invoice_date <= date_to_obj)
            except (ValueError, IndexError):
                pass
        
        # Filter out fully consumed fabrics if not showing them
        if not show_consumed:
            query = query.filter(
                or_(
                    InvoiceLine.yards_consumed.is_(None),
                    InvoiceLine.yards_consumed == 0,
                    InvoiceLine.yards_sent > InvoiceLine.yards_consumed
                )
            )

        # Execute query
        print("DEBUG: About to execute query")
        invoice_lines = query.all()
        print(f"DEBUG: Query executed, found {len(invoice_lines)} invoice lines")
        
        # Format response
        result = []
        for line in invoice_lines:
            # Use yards_sent and yards_consumed like the old Qt app
            yards_sent = line.yards_sent or line.quantity or 0
            yards_consumed = line.yards_consumed or 0
            pending = yards_sent - yards_consumed
            result.append({
                'id': line.id,
                'invoice_id': line.invoice_id,
                'invoice_number': line.invoice.invoice_number,
                'invoice_date': line.invoice.invoice_date.isoformat() if line.invoice.invoice_date else None,
                'tax_invoice_number': line.invoice.tax_invoice_number,
                'customer': {
                    'id': line.invoice.customer.id,
                    'short_name': line.invoice.customer.short_name,
                    'full_name': line.invoice.customer.full_name
                },
                'item_name': line.item_name,
                'quantity': float(line.quantity) if line.quantity else 0,
                'unit_price': float(line.unit_price) if line.unit_price else 0,
                'color': line.color,
                'delivery_note': line.delivery_note,
                'delivered_location': line.delivered_location,
                'yards_sent': float(yards_sent),
                'yards_consumed': float(yards_consumed),
                'pending': pending,
                'total_value': float(yards_sent * (line.unit_price or 0))
            })
        
        print(f"DEBUG: Returning {len(result)} results")
        return jsonify(result)
        
    except Exception as e:
        print(f"DEBUG: Error in get_invoices: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return {'error': str(e)}, 500

@invoices_bp.route('/', methods=['POST'])
def create_invoice_line():
    """Create a new invoice line"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_id', 'invoice_number', 'item_name', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return {'error': f'Missing required field: {field}'}, 400
        
        # Check if customer exists
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return {'error': 'Customer not found'}, 404
        
        # Create or get invoice
        invoice = Invoice.query.filter_by(
            invoice_number=data['invoice_number'],
            customer_id=data['customer_id']
        ).first()
        
        if not invoice:
            invoice = Invoice(
                invoice_number=data['invoice_number'],
                customer_id=data['customer_id'],
                invoice_date=datetime.now(),
                total_amount=float(data['quantity']) * float(data['unit_price']),
                status='open'
            )
            db.session.add(invoice)
            db.session.flush()  # Get the invoice ID
        
        # Create invoice line
        invoice_line = InvoiceLine(
            invoice_id=invoice.id,
            item_name=data['item_name'],
            quantity=float(data['quantity']),
            unit_price=float(data['unit_price']),
            color=data.get('color', ''),
            delivery_note=data.get('delivery_note', ''),
            delivered_location=data.get('delivered_location', ''),
            yards_sent=float(data['quantity']),
            yards_consumed=0.0
        )
        
        db.session.add(invoice_line)
        db.session.commit()
        
        return {'message': 'Invoice line created successfully', 'id': invoice_line.id}, 201
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/<int:line_id>', methods=['PUT'])
def update_invoice_line(line_id):
    """Update an invoice line"""
    try:
        line = InvoiceLine.query.get_or_404(line_id)
        data = request.get_json()
        
        # Update fields
        if 'item_name' in data:
            line.item_name = data['item_name']
        if 'quantity' in data:
            line.quantity = float(data['quantity'])
        if 'unit_price' in data:
            line.unit_price = float(data['unit_price'])
        if 'color' in data:
            line.color = data['color']
        if 'delivery_note' in data:
            line.delivery_note = data['delivery_note']
        if 'delivered_location' in data:
            line.delivered_location = data['delivered_location']
        
        db.session.commit()
        return {'message': 'Invoice line updated successfully'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/<int:line_id>', methods=['DELETE'])
def delete_invoice_line(line_id):
    """Delete an invoice line"""
    try:
        line = InvoiceLine.query.get_or_404(line_id)
        db.session.delete(line)
        db.session.commit()
        return {'message': 'Invoice line deleted successfully'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/assign-location', methods=['POST'])
def assign_delivered_location():
    """Assign delivered location to selected invoice lines"""
    try:
        data = request.get_json()
        line_ids = data.get('line_ids', [])
        location = data.get('location', '')
        
        if not line_ids:
            return {'error': 'No invoice lines selected'}, 400
        if not location:
            return {'error': 'Location is required'}, 400
        
        # Update all selected lines
        updated_count = InvoiceLine.query.filter(
            InvoiceLine.id.in_(line_ids)
        ).update({
            'delivered_location': location
        }, synchronize_session=False)
        
        db.session.commit()
        return {'message': f'Location assigned to {updated_count} invoice lines'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/assign-tax-invoice', methods=['POST'])
def assign_tax_invoice_number():
    """Assign tax invoice number to selected invoices"""
    try:
        data = request.get_json()
        invoice_ids = data.get('invoice_ids', [])
        tax_invoice_number = data.get('tax_invoice_number', '')
        
        if not invoice_ids:
            return {'error': 'No invoices selected'}, 400
        if not tax_invoice_number:
            return {'error': 'Tax invoice number is required'}, 400
        
        # Update all selected invoices
        updated_count = Invoice.query.filter(
            Invoice.id.in_(invoice_ids)
        ).update({
            'tax_invoice_number': tax_invoice_number
        }, synchronize_session=False)
        
        db.session.commit()
        return {'message': f'Tax invoice number assigned to {updated_count} invoices'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500


