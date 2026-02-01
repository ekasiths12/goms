from flask import Blueprint, request, jsonify, current_app
from app.models.invoice import Invoice, InvoiceLine
from app.models.customer import Customer
from app.models.delivery_location import DeliveryLocation
from app.models.commission_sale import CommissionSale
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from datetime import datetime
import traceback

# Import db from extensions
from extensions import db

invoices_bp = Blueprint('invoices', __name__)

# Server-side loading: default and max page size
DEFAULT_LIMIT = 50
MAX_LIMIT = 500


def _parse_multi_value(param):
    """Parse comma-separated query param into list of non-empty strings."""
    if not param or not str(param).strip():
        return []
    return [v.strip() for v in str(param).split(',') if v.strip()]

@invoices_bp.route('/test', methods=['GET'])
def test_invoices():
    """Test endpoint to check if the API is working"""
    try:
        return {'message': 'Invoices API is working', 'status': 'ok'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@invoices_bp.route('/count', methods=['GET'])
def count_invoices():
    """Count endpoint to check database tables"""
    try:
        invoice_count = db.session.query(Invoice).count()
        invoice_line_count = db.session.query(InvoiceLine).count()
        customer_count = db.session.query(Customer).count()
        
        return {
            'message': 'Database counts',
            'invoices': invoice_count,
            'invoice_lines': invoice_line_count,
            'customers': customer_count
        }, 200
    except Exception as e:
        return {'error': str(e)}, 500

@invoices_bp.route('/', methods=['GET'])
def get_invoices():
    """Get all invoices with line items and customer information. Supports server-side filtering and pagination."""
    try:
        # Get query parameters for filtering
        customer_filter = request.args.get('customer')
        invoice_number_filter = request.args.get('invoice_number')
        tax_invoice_filter = request.args.get('tax_invoice')
        item_code_filter = request.args.get('item_code')
        dn_filter = request.args.get('dn')
        location_filter = request.args.get('location')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        stock_status = request.args.get('stock_status', 'inStock')
        limit = min(int(request.args.get('limit', DEFAULT_LIMIT)), MAX_LIMIT)
        offset = max(0, int(request.args.get('offset', 0)))

        # Build query
        query = db.session.query(InvoiceLine).join(Invoice).join(Customer).options(
            db.joinedload(InvoiceLine.commission_sales)
        )

        # Multi-value filters (comma-separated): use IN; single value: ilike
        vals = _parse_multi_value(customer_filter)
        if vals:
            query = query.filter(Customer.short_name.in_(vals))
        elif customer_filter:
            query = query.filter(Customer.short_name.ilike(f'%{customer_filter}%'))
        vals = _parse_multi_value(invoice_number_filter)
        if vals:
            query = query.filter(Invoice.invoice_number.in_(vals))
        elif invoice_number_filter:
            query = query.filter(Invoice.invoice_number.ilike(f'%{invoice_number_filter}%'))
        vals = _parse_multi_value(tax_invoice_filter)
        if vals:
            query = query.filter(Invoice.tax_invoice_number.in_(vals))
        elif tax_invoice_filter:
            query = query.filter(Invoice.tax_invoice_number.ilike(f'%{tax_invoice_filter}%'))
        vals = _parse_multi_value(item_code_filter)
        if vals:
            query = query.filter(InvoiceLine.item_name.in_(vals))
        elif item_code_filter:
            query = query.filter(InvoiceLine.item_name.ilike(f'%{item_code_filter}%'))
        vals = _parse_multi_value(dn_filter)
        if vals:
            query = query.filter(InvoiceLine.delivery_note.in_(vals))
        elif dn_filter:
            query = query.filter(InvoiceLine.delivery_note.ilike(f'%{dn_filter}%'))
        vals = _parse_multi_value(location_filter)
        if vals:
            query = query.filter(InvoiceLine.delivered_location.in_(vals))
        elif location_filter:
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
        
        # Execute query
        invoice_lines = query.all()

        # Filter based on stock status (in-memory)
        if stock_status == 'inStock':
            invoice_lines = [line for line in invoice_lines if (line.yards_sent or 0) > ((line.yards_consumed or 0) + sum(cs.yards_sold for cs in line.commission_sales))]
        elif stock_status == 'noStock':
            invoice_lines = [line for line in invoice_lines if (line.yards_sent or 0) <= ((line.yards_consumed or 0) + sum(cs.yards_sold for cs in line.commission_sales))]

        # Format response (full list first for total count)
        result = []
        for line in invoice_lines:
            # Use yards_sent and yards_consumed like the old Qt app
            yards_sent = line.yards_sent or line.quantity or 0
            yards_consumed = line.yards_consumed or 0
            pending = line.pending_yards
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
                'total_used': float(yards_consumed) + sum(float(cs.yards_sold) for cs in line.commission_sales),
                'pending_yards': float(pending),
                'total_value': float(yards_sent * (line.unit_price or 0)),
                'total_commission_yards': sum(float(cs.yards_sold) for cs in line.commission_sales),
                'total_commission_amount': sum(float(cs.commission_amount) for cs in line.commission_sales),
                'commission_sales_count': len(line.commission_sales)
            })
        total = len(result)
        # Server-side pagination: return one page
        result = result[offset:offset + limit]
        return jsonify({'items': result, 'total': total})
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@invoices_bp.route('/filter-options', methods=['GET'])
def get_invoices_filter_options():
    """Return distinct values for filter dropdowns (scoped by date_from/date_to). Used for server-side loading."""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        base = db.session.query(InvoiceLine).join(Invoice).join(Customer).options(
            db.joinedload(InvoiceLine.commission_sales)
        )
        if date_from:
            try:
                s = date_from.strip()
                if len(s) == 8 and s.count('/') == 2:
                    d, m, y = s.split('/')
                    y = '20' + y if len(y) == 2 and int(y) < 50 else ('19' + y if len(y) == 2 else y)
                    s = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                date_from_obj = datetime.strptime(s[:10], '%Y-%m-%d')
                base = base.filter(Invoice.invoice_date >= date_from_obj)
            except (ValueError, IndexError):
                pass
        if date_to:
            try:
                s = date_to.strip()
                if len(s) == 8 and s.count('/') == 2:
                    d, m, y = s.split('/')
                    y = '20' + y if len(y) == 2 and int(y) < 50 else ('19' + y if len(y) == 2 else y)
                    s = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                date_to_obj = datetime.strptime(s[:10], '%Y-%m-%d')
                base = base.filter(Invoice.invoice_date <= date_to_obj)
            except (ValueError, IndexError):
                pass
        customers = [r[0] for r in base.with_entities(Customer.short_name).distinct().all() if r[0]]
        invoice_numbers = [r[0] for r in base.with_entities(Invoice.invoice_number).distinct().all() if r[0]]
        tax_invoices = [r[0] for r in base.with_entities(Invoice.tax_invoice_number).distinct().all() if r[0]]
        item_names = [r[0] for r in base.with_entities(InvoiceLine.item_name).distinct().all() if r[0]]
        delivery_notes = [r[0] for r in base.with_entities(InvoiceLine.delivery_note).distinct().all() if r[0]]
        locations = [r[0] for r in base.with_entities(InvoiceLine.delivered_location).distinct().all() if r[0]]
        return jsonify({
            'customers': sorted(customers),
            'invoice_numbers': sorted(invoice_numbers),
            'tax_invoice_numbers': sorted(tax_invoices),
            'item_names': sorted(item_names),
            'delivery_notes': sorted(delivery_notes),
            'locations': sorted(locations)
        })
    except Exception as e:
        if current_app.debug:
            traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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



@invoices_bp.route('/<int:line_id>/update', methods=['PUT'])
def update_invoice_line(line_id):
    """Update an invoice line"""
    try:
        data = request.get_json()
        
        # Get the invoice line
        invoice_line = InvoiceLine.query.get(line_id)
        if not invoice_line:
            return jsonify({'error': 'Invoice line not found'}), 404
        
        # Update fields
        if 'item_name' in data:
            invoice_line.item_name = data['item_name']
        if 'color' in data:
            invoice_line.color = data['color']
        if 'delivery_note' in data:
            invoice_line.delivery_note = data['delivery_note']
        if 'yards_sent' in data:
            invoice_line.yards_sent = data['yards_sent']
        if 'yards_consumed' in data:
            invoice_line.yards_consumed = data['yards_consumed']
        if 'unit_price' in data:
            invoice_line.unit_price = data['unit_price']
        if 'delivered_location' in data:
            invoice_line.delivered_location = data['delivered_location']
        
        # Update invoice total
        invoice = invoice_line.invoice
        if invoice:
            # Recalculate total based on all lines
            total = 0
            for line in invoice.invoice_lines:
                total += (line.yards_sent or 0) * (line.unit_price or 0)
            invoice.total_amount = total
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Invoice line updated successfully',
            'invoice_line': invoice_line.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating invoice line: {str(e)}'}), 500

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

@invoices_bp.route('/delete-multiple', methods=['POST'])
def delete_multiple_invoice_lines():
    """Delete multiple invoice lines"""
    try:
        data = request.get_json()
        line_ids = data.get('line_ids', [])
        
        if not line_ids:
            return {'error': 'No invoice lines selected'}, 400
        
        # Delete all selected lines
        deleted_count = InvoiceLine.query.filter(
            InvoiceLine.id.in_(line_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return {'message': f'{deleted_count} invoice line(s) deleted successfully'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/assign-location', methods=['POST'])
def assign_delivered_location():
    """Assign delivered location to selected invoice lines (like old Qt app)"""
    try:
        data = request.get_json()
        lines = data.get('lines', [])
        location = data.get('location', '')
        
        if not lines:
            return {'error': 'No invoice lines selected'}, 400
        if not location:
            return {'error': 'Location is required'}, 400
        
        updated_count = 0
        not_found = 0
        
        for line_data in lines:
            invoice_number = line_data.get('invoice_number')
            item_name = line_data.get('item_name')
            color = line_data.get('color')
            
            # Update using invoice_number, item_name, and color (like old Qt app)
            result = db.session.execute(
                db.text("""
                    UPDATE invoice_lines l
                    JOIN invoices i ON l.invoice_id = i.id
                    SET l.delivered_location = :location
                    WHERE i.invoice_number = :invoice_number 
                    AND l.item_name = :item_name 
                    AND l.color = :color
                """),
                {
                    'location': location,
                    'invoice_number': invoice_number,
                    'item_name': item_name,
                    'color': color
                }
            )
            
            if result.rowcount > 0:
                updated_count += result.rowcount
            else:
                not_found += 1
        
        db.session.commit()
        
        message = f"Location '{location}' assigned to {updated_count} invoice lines."
        if not_found > 0:
            message += f" {not_found} selected line(s) could not be found and were skipped."
        
        return {'message': message}, 200
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return {'error': str(e)}, 500

@invoices_bp.route('/remove-location', methods=['POST'])
def remove_delivered_location():
    """Remove delivered location from selected invoice lines"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400
        
        # Get selected line IDs
        line_ids = data.get('line_ids', [])
        if not line_ids:
            return {'error': 'No invoice lines selected'}, 400
        
        print(f"🔍 Removing location from {len(line_ids)} lines: {line_ids}")
        
        # Update invoice lines directly by ID
        updated_count = 0
        for line_id in line_ids:
            try:
                # Get the invoice line
                invoice_line = InvoiceLine.query.get(line_id)
                if invoice_line:
                    # Clear the delivered location
                    invoice_line.delivered_location = None
                    updated_count += 1
                    print(f"✅ Cleared location for line {line_id}")
                else:
                    print(f"❌ Line {line_id} not found")
            except Exception as e:
                print(f"❌ Error processing line {line_id}: {str(e)}")
        
        # Commit changes
        db.session.commit()
        
        message = f"Delivery location removed from {updated_count} invoice lines."
        print(f"✅ Remove location completed: {message}")
        
        return {'message': message, 'updated_count': updated_count}, 200
        
    except Exception as e:
        print(f"❌ Error in remove location: {str(e)}")
        db.session.rollback()
        return {'error': f'Failed to remove location: {str(e)}'}, 500

@invoices_bp.route('/assign-tax-invoice', methods=['POST'])
def assign_tax_invoice_number():
    """Assign tax invoice number to selected invoices (like old Qt app)"""
    try:
        data = request.get_json()
        base_invoice_number = data.get('base_invoice_number', '')
        tax_invoice_number = data.get('tax_invoice_number', '')
        
        if not base_invoice_number:
            return {'error': 'Base invoice number is required'}, 400
        
        # If user entered "0", clear the tax invoice number (set to NULL)
        if tax_invoice_number == "0":
            result = db.session.execute(
                db.text("UPDATE invoices SET tax_invoice_number = NULL WHERE invoice_number LIKE :base_invoice"),
                {'base_invoice': f"{base_invoice_number}%"}
            )
            affected_rows = result.rowcount
            db.session.commit()
            return {'message': f'Cleared tax invoice number for {affected_rows} invoices starting with {base_invoice_number}'}, 200
        else:
            # Update all invoices that start with the base invoice number
            result = db.session.execute(
                db.text("UPDATE invoices SET tax_invoice_number = :tax_invoice WHERE invoice_number LIKE :base_invoice"),
                {
                    'tax_invoice': tax_invoice_number,
                    'base_invoice': f"{base_invoice_number}%"
                }
            )
            affected_rows = result.rowcount
            db.session.commit()
            return {'message': f'Tax invoice number "{tax_invoice_number}" assigned to {affected_rows} invoices starting with {base_invoice_number}'}, 200
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return {'error': str(e)}, 500


# ===== DELIVERY LOCATION MANAGEMENT ENDPOINTS =====

@invoices_bp.route('/delivery-locations', methods=['GET'])
def get_delivery_locations():
    """Get all delivery locations"""
    try:
        locations = DeliveryLocation.get_all_locations()
        return jsonify([location.to_dict() for location in locations]), 200
    except Exception as e:
        return {'error': str(e)}, 500

@invoices_bp.route('/delivery-locations', methods=['POST'])
def create_delivery_location():
    """Create a new delivery location"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return {'error': 'Location name is required'}, 400
        
        # Check if location already exists
        existing = DeliveryLocation.get_by_name(name)
        if existing:
            return {'error': f'Location "{name}" already exists'}, 400
        
        location = DeliveryLocation.create_location(name)
        db.session.commit()
        
        return {'message': f'Location "{name}" created successfully', 'location': location.to_dict()}, 201
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/delivery-locations/<int:location_id>', methods=['DELETE'])
def delete_delivery_location(location_id):
    """Delete a delivery location"""
    try:
        success = DeliveryLocation.delete_location(location_id)
        if not success:
            return {'error': 'Location not found'}, 404
        
        db.session.commit()
        return {'message': 'Location deleted successfully'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500


# ===== COMMISSION SALES ENDPOINTS =====

@invoices_bp.route('/mark-commission-sale', methods=['POST'])
def mark_commission_sale():
    """Create a new commission sale"""
    try:
        data = request.get_json()
        line_id = data.get('line_id')
        yards_sold = data.get('yards_sold')
        sale_date = data.get('sale_date')
        
        if not line_id:
            return {'error': 'Line ID is required'}, 400
        if not yards_sold or yards_sold <= 0:
            return {'error': 'Yards sold must be greater than 0'}, 400
        if not sale_date:
            return {'error': 'Sale date is required'}, 400
        
        # Parse sale date
        try:
            sale_date_obj = datetime.strptime(sale_date, '%Y-%m-%d').date()
        except ValueError:
            return {'error': 'Invalid sale date format. Use YYYY-MM-DD'}, 400
        
        # Create commission sale
        commission_sale = CommissionSale.create_commission_sale(line_id, yards_sold, sale_date_obj)
        db.session.commit()
        
        return {
            'message': f'Successfully created commission sale for {yards_sold} yards',
            'serial_number': commission_sale.serial_number,
            'commission_amount': float(commission_sale.commission_amount),
            'remaining_pending': float(commission_sale.invoice_line.pending_yards)
        }, 200
        
    except ValueError as e:
        db.session.rollback()
        return {'error': str(e)}, 400
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/mark-commission-sale-bulk', methods=['POST'])
def mark_commission_sale_bulk():
    """Create multiple commission sales for selected invoice lines"""
    try:
        data = request.get_json()
        lines_data = data.get('lines', [])
        sale_date = data.get('sale_date')
        
        if not lines_data:
            return {'error': 'No lines data provided'}, 400
        if not sale_date:
            return {'error': 'Sale date is required'}, 400
        
        # Parse sale date
        try:
            sale_date_obj = datetime.strptime(sale_date, '%Y-%m-%d').date()
        except ValueError:
            return {'error': 'Invalid sale date format. Use YYYY-MM-DD'}, 400
        
        # Create bulk commission sales
        commission_sales, total_commission = CommissionSale.create_bulk_commission_sales(lines_data, sale_date_obj)
        db.session.commit()
        
        # Prepare response data
        response_data = []
        for commission_sale in commission_sales:
            response_data.append({
                'line_id': commission_sale.invoice_line_id,
                'serial_number': commission_sale.serial_number,
                'yards_sold': float(commission_sale.yards_sold),
                'commission_amount': float(commission_sale.commission_amount),
                'item_name': commission_sale.item_name,
                'color': commission_sale.color
            })
        
        return {
            'message': f'Successfully created {len(commission_sales)} commission sales',
            'commission_sales': response_data,
            'total_commission': float(total_commission),
            'sale_date': sale_date
        }, 200
        
    except ValueError as e:
        db.session.rollback()
        return {'error': str(e)}, 400
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@invoices_bp.route('/commission-sales', methods=['GET'])
def get_commission_sales():
    """Get all commission sales"""
    try:
        # Get query parameters for filtering
        customer_filter = request.args.get('customer')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = CommissionSale.query
        
        # Apply filters
        if customer_filter:
            query = query.filter(CommissionSale.customer_name.ilike(f'%{customer_filter}%'))
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(CommissionSale.sale_date >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(CommissionSale.sale_date <= date_to_obj)
            except ValueError:
                pass
        
        # Execute query
        commission_sales = query.order_by(CommissionSale.sale_date.desc()).all()
        
        # Convert to dictionary
        result = [sale.to_dict() for sale in commission_sales]
        
        return jsonify(result), 200
        
    except Exception as e:
        return {'error': str(e)}, 500

@invoices_bp.route('/delete-commission-sale', methods=['POST'])
def delete_commission_sale():
    """Delete a commission sale and revert fabric usage"""
    try:
        data = request.get_json()
        sale_id = data.get('sale_id')
        
        if not sale_id:
            return {'error': 'Sale ID is required'}, 400
        
        commission_sale = CommissionSale.query.get(sale_id)
        if not commission_sale:
            return {'error': 'Commission sale not found'}, 404
        
        commission_yards = commission_sale.yards_sold or 0
        invoice_line = commission_sale.invoice_line
        
        db.session.delete(commission_sale)
        db.session.commit()
        
        return {
            'message': f'Commission sale deleted successfully. Reverted {commission_yards} yards.',
            'remaining_pending': float(invoice_line.pending_yards)
        }, 200
        
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500