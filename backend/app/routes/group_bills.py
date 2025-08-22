from flask import Blueprint, request, jsonify, current_app, send_file
from app.models.group_bill import StitchingInvoiceGroup, StitchingInvoiceGroupLine
from app.models.stitching import StitchingInvoice
from app.models.packing_list import PackingList, PackingListLine
from app.models.customer import Customer
from app.models.serial_counter import SerialCounter
from datetime import datetime, date
import json
import os
import shutil
from fpdf import FPDF
from extensions import db

group_bills_bp = Blueprint('group_bills', __name__)

@group_bills_bp.route('/', methods=['GET'])
def get_group_bills():
    """Get all group bills with optional filters"""
    try:
        # Get query parameters for filtering
        customer = request.args.get('customer')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Get sorting parameters
        sort_column = request.args.get('sort_column', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Build query
        query = StitchingInvoiceGroup.query.join(Customer)
        
        if customer:
            query = query.filter(Customer.short_name.ilike(f'%{customer}%'))
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(db.func.date(StitchingInvoiceGroup.created_at) >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(db.func.date(StitchingInvoiceGroup.created_at) <= date_to_obj)
            except ValueError:
                pass
        
        # Apply sorting
        sort_direction_func = db.desc if sort_direction.lower() == 'desc' else db.asc
        
        # Map frontend column names to database columns
        sort_mapping = {
            'created_at': StitchingInvoiceGroup.created_at,
            'group_billing_note_serial': StitchingInvoiceGroup.group_billing_note_serial,
            'customer': Customer.short_name,
            'invoice_date': StitchingInvoiceGroup.invoice_date,
            'total_amount': StitchingInvoiceGroup.total_amount,
            'withholding_tax_amount': StitchingInvoiceGroup.withholding_tax_amount,
            'net_amount': StitchingInvoiceGroup.net_amount,
            'status': StitchingInvoiceGroup.status
        }
        
        if sort_column in sort_mapping:
            query = query.order_by(sort_direction_func(sort_mapping[sort_column]))
        else:
            # Default sorting by creation date
            query = query.order_by(sort_direction_func(StitchingInvoiceGroup.created_at))
        
        # Execute query
        group_bills = query.all()
        
        # Convert to dictionary format with detailed structure
        result = []
        for group_bill in group_bills:
            group_dict = group_bill.to_dict()
            
            # Calculate totals
            totals = group_bill.calculate_totals()
            group_dict.update(totals)
            
            # Add detailed structure for multi-level display
            details = get_group_bill_details(group_bill.id)
            group_dict['details'] = details
            
            result.append(group_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@group_bills_bp.route('/create', methods=['POST'])
def create_group_bill():
    """Create a new group bill from selected packing lists"""
    try:
        data = request.get_json()
        packing_list_ids = data.get('packing_list_ids', [])
        invoice_date = data.get('invoice_date')
        stitching_comments = data.get('stitching_comments', '')
        fabric_comments = data.get('fabric_comments', '')
        apply_withholding_tax = data.get('apply_withholding_tax', True)
        
        if not packing_list_ids:
            return jsonify({'error': 'No packing list IDs provided'}), 400
        
        # Generate group billing note serial number
        group_number = generate_serial_number("GBN")
        
        # Get customer_id from the first packing list
        first_packing_list = PackingList.query.get(packing_list_ids[0])
        if not first_packing_list:
            return jsonify({'error': 'Could not determine customer for selected packing lists'}), 400
        
        customer_id = first_packing_list.customer_id
        
        # Parse invoice date
        invoice_date_obj = None
        if invoice_date:
            try:
                invoice_date_obj = datetime.strptime(invoice_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid invoice date format'}), 400
        
        # Create group bill
        group_bill = StitchingInvoiceGroup(
            group_number=group_number,
            customer_id=customer_id,
            invoice_date=invoice_date_obj,
            stitching_comments=stitching_comments,
            fabric_comments=fabric_comments
        )
        
        db.session.add(group_bill)
        db.session.flush()  # Get the group_id
        
        # Get all stitching records from the selected packing lists
        stitching_ids = []
        for packing_list_id in packing_list_ids:
            packing_list_lines = PackingListLine.query.filter_by(packing_list_id=packing_list_id).all()
            for line in packing_list_lines:
                if line.stitching_invoice_id:
                    stitching_ids.append(line.stitching_invoice_id)
        
        # Create group lines and update stitching invoices
        for stitching_id in stitching_ids:
            group_line = StitchingInvoiceGroupLine(
                group_id=group_bill.id,
                stitching_invoice_id=stitching_id
            )
            db.session.add(group_line)
            
            # Update stitching invoice to mark it as grouped
            stitching_invoice = StitchingInvoice.query.get(stitching_id)
            if stitching_invoice:
                stitching_invoice.billing_group_id = group_bill.id
        
        db.session.commit()
        
        # Generate PDFs
        generate_stitching_fee_pdf(group_bill.id, apply_withholding_tax)
        generate_fabric_used_pdf(group_bill.id)
        
        return jsonify({
            'success': True,
            'message': f'Group bill {group_number} created successfully',
            'group_bill': group_bill.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@group_bills_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_group_bill(group_id):
    """Delete a group bill and ungroup all stitching records"""
    try:
        group_bill = StitchingInvoiceGroup.query.get(group_id)
        if not group_bill:
            return jsonify({'error': 'Group bill not found'}), 404
        
        group_number = group_bill.group_number
        
        # Get all stitching records in this group
        stitching_ids = [line.stitching_invoice_id for line in group_bill.group_lines]
        
        # Update stitching invoices to remove billing_group_id
        for stitching_id in stitching_ids:
            stitching_invoice = StitchingInvoice.query.get(stitching_id)
            if stitching_invoice:
                stitching_invoice.billing_group_id = None
        
        # Delete group bill PDF files
        safe_group_number = group_number.replace('/', '_').replace('\\', '_')
        group_dir = os.path.join('group_bills', safe_group_number)
        if os.path.exists(group_dir):
            shutil.rmtree(group_dir)
        
        # Delete group bill from database
        db.session.delete(group_bill)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Group bill {group_number} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@group_bills_bp.route('/<int:group_id>/stitching-pdf', methods=['GET'])
def get_stitching_pdf(group_id):
    """Generate and return stitching fee PDF for a group bill"""
    try:
        group_bill = StitchingInvoiceGroup.query.get(group_id)
        if not group_bill:
            return jsonify({'error': 'Group bill not found'}), 404
        
        # Generate PDF
        pdf_path = generate_stitching_fee_pdf(group_id, request.args.get('apply_withholding_tax', 'true').lower() == 'true')
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{group_bill.group_number}_stitching.pdf")
        else:
            return jsonify({'error': 'PDF generation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@group_bills_bp.route('/<int:group_id>/fabric-pdf', methods=['GET'])
def get_fabric_pdf(group_id):
    """Generate and return fabric used PDF for a group bill"""
    try:
        group_bill = StitchingInvoiceGroup.query.get(group_id)
        if not group_bill:
            return jsonify({'error': 'Group bill not found'}), 404
        
        # Generate PDF
        pdf_path = generate_fabric_used_pdf(group_id)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{group_bill.group_number}_fabric.pdf")
        else:
            return jsonify({'error': 'PDF generation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_serial_number(prefix):
    """Generate a unique serial number with the given prefix"""
    return SerialCounter.generate_serial_number(prefix)

def generate_stitching_fee_pdf(group_id, apply_withholding_tax=False):
    """Generate stitching fee PDF for a group bill"""
    group_bill = StitchingInvoiceGroup.query.get(group_id)
    if not group_bill:
        raise ValueError("Group bill not found")
    
    # Get all stitching records in this group
    lines = []
    for group_line in group_bill.group_lines:
        stitching_invoice = group_line.stitching_invoice
        if stitching_invoice:
            line_data = {
                'id': stitching_invoice.id,
                'stitching_invoice_number': stitching_invoice.stitching_invoice_number,
                'stitched_item': stitching_invoice.stitched_item,
                'fabric_name': stitching_invoice.item_name,
                'color': stitching_invoice.invoice_line.color if stitching_invoice.invoice_line else '',
                'price': float(stitching_invoice.price or 0),
                'total_value': float(stitching_invoice.total_value or 0),
                'add_vat': stitching_invoice.add_vat,
                'size_qty': stitching_invoice.get_size_qty(),
                'packing_list_serial': None,
                'pl_created_at': None,
                'pl_tax_invoice_number': None
            }
            
            # Get packing list information
            packing_list_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_invoice.id).first()
            if packing_list_line and packing_list_line.packing_list:
                line_data['packing_list_serial'] = packing_list_line.packing_list.packing_list_serial
                line_data['pl_created_at'] = packing_list_line.packing_list.created_at
                line_data['pl_tax_invoice_number'] = packing_list_line.packing_list.tax_invoice_number
            
            lines.append(line_data)
    
    # Group by tax invoice number
    tax_groups = {}
    for line in lines:
        tax_inv = line.get('pl_tax_invoice_number')
        if tax_inv not in tax_groups:
            tax_groups[tax_inv] = []
        tax_groups[tax_inv].append(line)
    
    # Create PDF
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 8, "M.S.K Textile Trading   |   Stitching Invoice", ln=1, align='C')
    pdf.set_font("Arial", '', 9)
    
    display_date = group_bill.invoice_date or group_bill.created_at
    group_info = f"Group: {group_bill.group_number}   Customer: {group_bill.customer.short_name}   Date: {format_ddmmyy(display_date)}"
    pdf.cell(0, 7, group_info, ln=1, align='C')
    pdf.ln(1)
    
    # Comments
    if group_bill.stitching_comments:
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Comments:", ln=1)
        pdf.set_font("Arial", '', 9)
        
        comment_lines = wrap_text(group_bill.stitching_comments, 180)
        for line in comment_lines:
            pdf.cell(0, 5, line, ln=1)
        pdf.ln(1)
    
    # Stitching items section
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "--- STITCHING ITEMS ---", ln=1)
    
    grand_total = 0
    
    # Print all tax groups
    for tax_inv, group_lines in tax_groups.items():
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(0, 6, f"Tax Invoice #: {tax_inv if tax_inv else '(None)'}", ln=1)
        pdf.set_font("Arial", '', 7)
        
        # Group by packing list
        pl_groups = {}
        for line in group_lines:
            pl_key = (line.get('packing_list_serial', ''), line.get('pl_created_at'))
            if pl_key not in pl_groups:
                pl_groups[pl_key] = []
            pl_groups[pl_key].append(line)
        
        for (pl_serial, pl_created_at), pl_lines in pl_groups.items():
            # Sub-header for each packing list group
            pdf.set_font("Arial", 'B', 7)
            pl_date = format_ddmmyy(pl_created_at) if pl_created_at else ''
            pdf.cell(0, 5, f"Tax Invoice #: {tax_inv if tax_inv else '(None)'}    Packing List #: {pl_serial}    Delivery Date: {pl_date}", ln=1)
            
            # Table header
            pdf.set_font("Arial", 'B', 8)
            col_widths = [20, 18, 28, 32, 18, 14, 16, 20]
            pdf.cell(col_widths[0], 6, "Serial", 1)
            pdf.cell(col_widths[1], 6, "Img", 1)
            pdf.cell(col_widths[2], 6, "Garment", 1)
            pdf.cell(col_widths[3], 6, "Fabric", 1)
            pdf.cell(col_widths[4], 6, "Color", 1)
            pdf.cell(col_widths[5], 6, "Tot", 1)
            pdf.cell(col_widths[6], 6, "Price", 1)
            pdf.cell(col_widths[7], 6, "Value", 1)
            pdf.ln()
            
            pdf.set_font("Arial", '', 7)
            pl_total = 0
            
            for line in pl_lines:
                pdf.cell(col_widths[0], 18, str(line['stitching_invoice_number'] or ''), 1)
                pdf.cell(col_widths[1], 18, '', 1)  # Image placeholder
                pdf.cell(col_widths[2], 18, str(line['stitched_item'] or ''), 1)
                pdf.cell(col_widths[3], 18, str(line['fabric_name'] or ''), 1)
                pdf.cell(col_widths[4], 18, str(line['color'] or ''), 1)
                
                total_qty = sum(line['size_qty'].values())
                pdf.cell(col_widths[5], 18, str(total_qty), 1)
                
                # Calculate VAT-inclusive price
                base_price = line['price']
                if line.get('add_vat'):
                    vat_amount = base_price * 0.07
                    vat_inclusive_price = base_price + vat_amount
                else:
                    vat_inclusive_price = base_price
                
                pdf.cell(col_widths[6], 18, f"{vat_inclusive_price:,.2f}", 1)
                pdf.cell(col_widths[7], 18, f"{line['total_value']:,.2f}", 1)
                pl_total += line['total_value']
                pdf.ln(18)
            
            pdf.set_font("Arial", 'B', 7)
            pdf.cell(0, 6, f"Total for Tax Invoice {tax_inv if tax_inv else '(None)'}: {pl_total:,.2f} THB", ln=1)
            pdf.set_font("Arial", '', 7)
            pdf.ln(2)
            grand_total += pl_total
    
    # Calculate totals
    stitching_vat_total = 0
    stitching_base_total = 0
    
    for line in lines:
        base_price = line['price']
        if line.get('add_vat'):
            vat_amount = base_price * 0.07
            stitching_vat_total += vat_amount
        stitching_base_total += base_price
    
    # Summary section
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "--- SUMMARY ---", ln=1)
    pdf.set_font("Arial", '', 9)
    
    pdf.cell(80, 6, "Stitching Subtotal:", 0)
    pdf.cell(40, 6, f"{stitching_base_total:,.2f} THB", 0)
    pdf.ln()
    
    if stitching_vat_total > 0:
        pdf.cell(80, 6, "VAT (7%):", 0)
        pdf.cell(40, 6, f"{stitching_vat_total:,.2f} THB", 0)
        pdf.ln()
    
    withholding_tax = 0
    if apply_withholding_tax:
        withholding_tax = grand_total * 0.03
        pdf.cell(80, 6, "Withholding Tax (3%):", 0)
        pdf.cell(40, 6, f"{withholding_tax:,.2f} THB", 0)
        pdf.ln()
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(80, 8, "GRAND TOTAL:", 0)
    pdf.cell(40, 8, f"{grand_total:,.2f} THB", 0)
    pdf.ln()
    
    # Save PDF
    safe_group_number = group_bill.group_number.replace('/', '_').replace('\\', '_')
    group_dir = os.path.join('group_bills', safe_group_number)
    os.makedirs(group_dir, exist_ok=True)
    
    pdf_path = os.path.join(group_dir, f"{group_bill.group_number}_stitching.pdf")
    pdf.output(pdf_path)
    
    return pdf_path

def generate_fabric_used_pdf(group_id):
    """Generate fabric used PDF for a group bill"""
    group_bill = StitchingInvoiceGroup.query.get(group_id)
    if not group_bill:
        raise ValueError("Group bill not found")
    
    # Get all stitching records in this group
    lines = []
    for group_line in group_bill.group_lines:
        stitching_invoice = group_line.stitching_invoice
        if stitching_invoice and stitching_invoice.invoice_line:
            line_data = {
                'stitching_invoice_number': stitching_invoice.stitching_invoice_number,
                'stitched_item': stitching_invoice.stitched_item,
                'fabric_name': stitching_invoice.invoice_line.item_name,
                'color': stitching_invoice.invoice_line.color,
                'yards_consumed': float(stitching_invoice.yard_consumed or 0),
                'unit_price': float(stitching_invoice.invoice_line.unit_price or 0),
                'total_value': float(stitching_invoice.yard_consumed or 0) * float(stitching_invoice.invoice_line.unit_price or 0),
                'packing_list_serial': None
            }
            
            # Get packing list information
            packing_list_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_invoice.id).first()
            if packing_list_line and packing_list_line.packing_list:
                line_data['packing_list_serial'] = packing_list_line.packing_list.packing_list_serial
            
            lines.append(line_data)
    
    # Create PDF
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 8, "M.S.K Textile Trading   |   Fabric Used Invoice", ln=1, align='C')
    pdf.set_font("Arial", '', 9)
    
    display_date = group_bill.invoice_date or group_bill.created_at
    group_info = f"Group: {group_bill.group_number}   Customer: {group_bill.customer.short_name}   Date: {format_ddmmyy(display_date)}"
    pdf.cell(0, 7, group_info, ln=1, align='C')
    pdf.ln(1)
    
    # Comments
    if group_bill.fabric_comments:
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Comments:", ln=1)
        pdf.set_font("Arial", '', 9)
        
        comment_lines = wrap_text(group_bill.fabric_comments, 180)
        for line in comment_lines:
            pdf.cell(0, 5, line, ln=1)
        pdf.ln(1)
    
    # Fabric items section
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "--- FABRIC ITEMS ---", ln=1)
    
    # Table header
    pdf.set_font("Arial", 'B', 8)
    col_widths = [25, 35, 25, 20, 25, 30]
    pdf.cell(col_widths[0], 6, "Serial", 1)
    pdf.cell(col_widths[1], 6, "Garment", 1)
    pdf.cell(col_widths[2], 6, "Fabric", 1)
    pdf.cell(col_widths[3], 6, "Color", 1)
    pdf.cell(col_widths[4], 6, "Yards", 1)
    pdf.cell(col_widths[5], 6, "Value", 1)
    pdf.ln()
    
    pdf.set_font("Arial", '', 7)
    grand_total = 0
    
    for line in lines:
        pdf.cell(col_widths[0], 6, str(line['stitching_invoice_number'] or ''), 1)
        pdf.cell(col_widths[1], 6, str(line['stitched_item'] or ''), 1)
        pdf.cell(col_widths[2], 6, str(line['fabric_name'] or ''), 1)
        pdf.cell(col_widths[3], 6, str(line['color'] or ''), 1)
        pdf.cell(col_widths[4], 6, f"{line['yards_consumed']:.2f}", 1)
        pdf.cell(col_widths[5], 6, f"{line['total_value']:,.2f}", 1)
        grand_total += line['total_value']
        pdf.ln()
    
    # Total
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, f"TOTAL: {grand_total:,.2f} THB", ln=1)
    
    # Save PDF
    safe_group_number = group_bill.group_number.replace('/', '_').replace('\\', '_')
    group_dir = os.path.join('group_bills', safe_group_number)
    os.makedirs(group_dir, exist_ok=True)
    
    pdf_path = os.path.join(group_dir, f"{group_bill.group_number}_fabric.pdf")
    pdf.output(pdf_path)
    
    return pdf_path

def format_ddmmyy(date_obj):
    """Format date as DD/MM/YY"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%d/%m/%y')
    return str(date_obj)

def wrap_text(text, max_width):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_width:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def get_group_bill_details(group_id):
    """Get detailed structure for group bill multi-level display"""
    try:
        # Get the group bill
        group_bill = StitchingInvoiceGroup.query.get(group_id)
        if not group_bill:
            print(f"Group bill {group_id} not found")
            return {
                'total_fabric_used': 0,
                'total_fabric_value': 0,
                'total_stitching_value': 0,
                'total_items': 0,
                'size_totals': {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0},
                'packing_lists': {},
                'individual_records': []
            }
        
        print(f"Found group bill {group_bill.group_number} with {len(group_bill.group_lines)} lines")
        
        # Get all stitching records for this group using ORM
        records = []
        for group_line in group_bill.group_lines:
            stitching_invoice = group_line.stitching_invoice
            if stitching_invoice:
                # Get packing list information
                packing_list_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_invoice.id).first()
                packing_list = packing_list_line.packing_list if packing_list_line else None
                
                record_dict = {
                    'id': stitching_invoice.id,
                    'stitching_invoice_number': stitching_invoice.stitching_invoice_number,
                    'stitched_item': stitching_invoice.stitched_item,
                    'item_name': stitching_invoice.item_name,
                    'color': stitching_invoice.invoice_line.color if stitching_invoice.invoice_line else None,
                    'tax_invoice_number': stitching_invoice.invoice_line.invoice.tax_invoice_number if stitching_invoice.invoice_line and stitching_invoice.invoice_line.invoice else None,
                    'fabric_invoice_number': stitching_invoice.invoice_line.invoice.invoice_number if stitching_invoice.invoice_line and stitching_invoice.invoice_line.invoice else None,
                    'delivery_note': stitching_invoice.invoice_line.delivery_note if stitching_invoice.invoice_line else None,
                    'customer': stitching_invoice.invoice_line.invoice.customer.short_name if stitching_invoice.invoice_line and stitching_invoice.invoice_line.invoice and stitching_invoice.invoice_line.invoice.customer else None,
                    'fabric_unit_price': float(stitching_invoice.invoice_line.unit_price) if stitching_invoice.invoice_line else 0,
                    'yard_consumed': float(stitching_invoice.yard_consumed) if stitching_invoice.yard_consumed else 0,
                    'price': float(stitching_invoice.price) if stitching_invoice.price else 0,
                    'total_value': float(stitching_invoice.total_value) if stitching_invoice.total_value else 0,
                    'size_qty_json': stitching_invoice.size_qty_json,
                    'created_at': stitching_invoice.created_at,
                    'packing_list_serial': packing_list.packing_list_serial if packing_list else None,
                    'pl_created_at': packing_list.created_at if packing_list else None,
                    'pl_tax_invoice_number': packing_list.tax_invoice_number if packing_list else None
                }
                records.append(record_dict)
        
        print(f"Processed {len(records)} records")
        
        # Group records by packing list
        packing_lists = {}
        total_fabric_used = 0
        total_fabric_value = 0
        total_stitching_value = 0
        total_items = 0
        size_totals = {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0}
        
        for rec in records:
            pl_serial = rec.get('packing_list_serial') or 'No PL'
            if pl_serial not in packing_lists:
                packing_lists[pl_serial] = {
                    'fabric_used': 0,
                    'fabric_value': 0,
                    'stitching_value': 0,
                    'total_items': 0,
                    'size_totals': {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0},
                    'created_at': rec.get('pl_created_at')
                }
            
            yards_consumed = rec.get('yard_consumed') or 0
            fabric_cost = rec.get('fabric_unit_price') or 0
            fabric_value = fabric_cost * yards_consumed
            stitching_value = rec.get('total_value') or 0
            
            total_fabric_used += yards_consumed
            total_fabric_value += fabric_value
            total_stitching_value += stitching_value
            
            packing_lists[pl_serial]['fabric_used'] += yards_consumed
            packing_lists[pl_serial]['fabric_value'] += fabric_value
            packing_lists[pl_serial]['stitching_value'] += stitching_value
            
            try:
                size_qty = eval(rec.get('size_qty_json')) if rec.get('size_qty_json') else {}
            except Exception:
                size_qty = {}
            
            for sz in size_totals:
                size_totals[sz] += size_qty.get(sz, 0)
                packing_lists[pl_serial]['size_totals'][sz] += size_qty.get(sz, 0)
            
            pl_items = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            total_items += pl_items
            packing_lists[pl_serial]['total_items'] += pl_items
        
        return {
            'total_fabric_used': total_fabric_used,
            'total_fabric_value': total_fabric_value,
            'total_stitching_value': total_stitching_value,
            'total_items': total_items,
            'size_totals': size_totals,
            'packing_lists': packing_lists,
            'individual_records': records
        }
        
    except Exception as e:
        print(f"Error getting group bill details: {e}")
        return {
            'total_fabric_used': 0,
            'total_fabric_value': 0,
            'total_stitching_value': 0,
            'total_items': 0,
            'size_totals': {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "XXXL": 0},
            'packing_lists': {},
            'individual_records': []
        }