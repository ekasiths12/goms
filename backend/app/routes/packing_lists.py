from flask import Blueprint, request, jsonify, current_app, send_file
from app.models.packing_list import PackingList, PackingListLine
from app.models.stitching import StitchingInvoice, GarmentFabric, LiningFabric
from app.models.invoice import InvoiceLine, Invoice
from app.models.customer import Customer
from app.models.serial_counter import SerialCounter
from app.models.image import Image
from datetime import datetime, date
import json
import os
import shutil
from fpdf import FPDF
from extensions import db

packing_lists_bp = Blueprint('packing_lists', __name__)

@packing_lists_bp.route('/', methods=['GET'])
def get_packing_lists():
    """Get all packing lists with optional filters"""
    try:
        # Get query parameters for filtering
        pl_serial = request.args.get('pl_serial')
        stitch_serial = request.args.get('stitch_serial')
        fabric_name = request.args.get('fabric_name')
        customer = request.args.get('customer')
        tax_invoice = request.args.get('tax_invoice')
        fabric_invoice = request.args.get('fabric_invoice')
        fabric_dn = request.args.get('fabric_dn')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        billing_status = request.args.get('billing_status', 'all')  # all, billed, unbilled
        
        # Build query
        query = PackingList.query.join(Customer)
        
        if pl_serial:
            query = query.filter(PackingList.packing_list_serial.ilike(f'%{pl_serial}%'))
        
        if stitch_serial:
            query = query.join(PackingListLine).join(StitchingInvoice).filter(
                StitchingInvoice.stitching_invoice_number.ilike(f'%{stitch_serial}%')
            )
        
        if fabric_name:
            query = query.join(PackingListLine).join(StitchingInvoice).join(InvoiceLine).filter(
                InvoiceLine.item_name.ilike(f'%{fabric_name}%')
            )
        
        if customer:
            query = query.filter(Customer.short_name.ilike(f'%{customer}%'))
        
        if tax_invoice:
            query = query.join(PackingListLine).join(StitchingInvoice).join(InvoiceLine).join(Invoice).filter(
                Invoice.tax_invoice_number.ilike(f'%{tax_invoice}%')
            )
        
        if fabric_invoice:
            query = query.join(PackingListLine).join(StitchingInvoice).join(InvoiceLine).join(Invoice).filter(
                Invoice.invoice_number.ilike(f'%{fabric_invoice}%')
            )
        
        if fabric_dn:
            query = query.join(PackingListLine).join(StitchingInvoice).join(InvoiceLine).filter(
                InvoiceLine.delivery_note.ilike(f'%{fabric_dn}%')
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(db.func.date(PackingList.created_at) >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(db.func.date(PackingList.created_at) <= date_to_obj)
            except ValueError:
                pass
        
        # Apply billing status filter
        if billing_status == 'billed':
            query = query.filter(
                PackingList.id.in_(
                    db.session.query(PackingListLine.packing_list_id)
                    .join(StitchingInvoice)
                    .filter(StitchingInvoice.billing_group_id.isnot(None))
                )
            )
        elif billing_status == 'unbilled':
            query = query.filter(
                ~PackingList.id.in_(
                    db.session.query(PackingListLine.packing_list_id)
                    .join(StitchingInvoice)
                    .filter(StitchingInvoice.billing_group_id.isnot(None))
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(PackingList.created_at.desc())
        
        # Execute query with distinct to avoid duplicates from joins
        packing_lists = query.distinct().all()
        
        # Convert to dictionary format with detailed data for treeview
        result = []
        for pl in packing_lists:
            pl_dict = pl.to_dict()
            
            # Get detailed packing list lines
            lines = []
            for line in pl.packing_list_lines:
                line_dict = line.to_dict()
                
                # Add additional data for treeview display
                if line.stitching_invoice:
                    stitching = line.stitching_invoice
                    
                    # Add garment fabrics and lining fabrics
                    line_dict['garment_fabrics'] = [fabric.to_dict() for fabric in stitching.garment_fabrics]
                    line_dict['lining_fabrics'] = [lining.to_dict() for lining in stitching.lining_fabrics]
                    
                    # Calculate garment cost per piece
                    size_qty = stitching.get_size_qty()
                    total_qty = sum(size_qty.values())
                    
                    if total_qty > 0:
                        # Main fabric cost
                        main_fabric_cost = 0
                        if stitching.yard_consumed and stitching.invoice_line and stitching.invoice_line.unit_price:
                            main_fabric_cost = float(stitching.yard_consumed) * float(stitching.invoice_line.unit_price)
                        
                        # Multi-fabric costs
                        multi_fabric_cost = sum(float(fabric.total_fabric_cost or 0) for fabric in stitching.garment_fabrics)
                        
                        # Lining costs
                        lining_cost = sum(float(lining.total_cost or 0) for lining in stitching.lining_fabrics)
                        
                        # Total fabric cost
                        total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
                        fabric_cost_per_garment = total_fabric_cost / total_qty
                        
                        # Sewing cost with VAT if applicable
                        sewing_price = float(stitching.price or 0)
                        if stitching.add_vat:
                            sewing_cost_per_garment = sewing_price * 1.07
                        else:
                            sewing_cost_per_garment = sewing_price
                        
                        line_dict['garment_cost_per_piece'] = fabric_cost_per_garment + sewing_cost_per_garment
                    else:
                        line_dict['garment_cost_per_piece'] = 0
                
                lines.append(line_dict)
            
            pl_dict['lines'] = lines
            result.append(pl_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@packing_lists_bp.route('/generate', methods=['POST'])
def create_packing_list():
    """Create a new packing list from selected stitching records"""
    try:
        data = request.get_json()
        stitching_ids = data.get('stitching_ids', [])
        delivery_date = data.get('delivery_date')
        comments = data.get('comments', '')
        
        if not stitching_ids:
            return jsonify({'error': 'No stitching records provided'}), 400
        
        # Validate that all stitching records exist and are not already in packing lists
        stitching_records = []
        customer_id = None
        
        for stitching_id in stitching_ids:
            stitching_record = StitchingInvoice.query.get(stitching_id)
            if not stitching_record:
                return jsonify({'error': f'Stitching record with ID {stitching_id} not found'}), 400
            
            # Check if already in a packing list
            existing_pl_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_id).first()
            if existing_pl_line:
                return jsonify({'error': f'Stitching record {stitching_record.stitching_invoice_number} is already in packing list {existing_pl_line.packing_list.packing_list_serial}'}), 400
            
            # Get customer_id from the first record
            if customer_id is None and stitching_record.invoice_line and stitching_record.invoice_line.invoice:
                customer_id = stitching_record.invoice_line.invoice.customer_id
            
            stitching_records.append(stitching_record)
        
        if not customer_id:
            return jsonify({'error': 'Could not determine customer for selected records'}), 400
        
        # Parse delivery date
        delivery_date_obj = None
        if delivery_date:
            try:
                delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid delivery date format. Use YYYY-MM-DD'}), 400
        
        # Generate packing list serial number
        packing_list_serial = SerialCounter.generate_serial_number('PL')
        
        # Create packing list
        packing_list = PackingList(
            packing_list_serial=packing_list_serial,
            customer_id=customer_id,
            delivery_date=delivery_date_obj,
            comments=comments
        )
        db.session.add(packing_list)
        db.session.flush()  # Get the ID
        
        # Link stitching records to packing list
        for stitching_record in stitching_records:
            packing_list_line = PackingListLine(
                packing_list_id=packing_list.id,
                stitching_invoice_id=stitching_record.id
            )
            db.session.add(packing_list_line)
        
        # Calculate and update totals
        packing_list.calculate_totals()
        
        db.session.commit()
        
        # Generate PDF without garment cost by default
        pdf_path = generate_packing_list_pdf(packing_list.id, show_garment_cost=False)
        
        return jsonify({
            'message': f'Packing list {packing_list_serial} created with {len(stitching_ids)} records and {packing_list.total_items} items',
            'packing_list': packing_list.to_dict(),
            'pdf_path': pdf_path
        })
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500

@packing_lists_bp.route('/<int:packing_list_id>', methods=['DELETE'])
def delete_packing_list(packing_list_id):
    """Delete a packing list and ungroup stitching records"""
    try:
        packing_list = PackingList.query.get_or_404(packing_list_id)
        
        # Get all stitching records in this packing list
        stitching_records = []
        for line in packing_list.packing_list_lines:
            if line.stitching_invoice:
                stitching_records.append(line.stitching_invoice)
        
        # Remove from group bills if any
        from app.models.group_bill import StitchingInvoiceGroupLine
        for stitching in stitching_records:
            # Remove from group bill lines
            StitchingInvoiceGroupLine.query.filter_by(stitching_invoice_id=stitching.id).delete()
            
            # Set billing_group_id to NULL
            stitching.billing_group_id = None
        
        # Delete packing list PDF files
        if packing_list.packing_list_serial:
            safe_serial = packing_list.packing_list_serial.replace('/', '_')
            pdf_dir = os.path.join('packing_lists', safe_serial)
            pdf_file = os.path.join(pdf_dir, f"{packing_list.packing_list_serial}.pdf")
            
            try:
                if os.path.exists(pdf_file):
                    os.remove(pdf_file)
                # Remove directory if empty
                if os.path.exists(pdf_dir) and not os.listdir(pdf_dir):
                    os.rmdir(pdf_dir)
            except Exception as e:
                print(f"Warning: Could not delete PDF file {pdf_file}: {e}")
        
        # Delete packing list (cascade will handle packing_list_lines)
        db.session.delete(packing_list)
        db.session.commit()
        
        return jsonify({
            'message': f'Packing list {packing_list.packing_list_serial} deleted successfully'
        })
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500

@packing_lists_bp.route('/<int:packing_list_id>/pdf', methods=['GET'])
def get_packing_list_pdf(packing_list_id):
    """Generate and return packing list PDF"""
    try:
        show_garment_cost = request.args.get('show_cost', 'false').lower() == 'true'
        
        pdf_path = generate_packing_list_pdf(packing_list_id, show_garment_cost=show_garment_cost)
        
        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF generation failed'}), 500
        
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@packing_lists_bp.route('/assign-tax-invoice', methods=['POST'])
def assign_tax_invoice():
    """Assign tax invoice number to packing lists"""
    try:
        data = request.get_json()
        packing_list_ids = data.get('packing_list_ids', [])
        tax_invoice_number = data.get('tax_invoice_number')
        
        if not packing_list_ids:
            return jsonify({'success': False, 'error': 'No packing list IDs provided'}), 400
        
        # Update packing lists with tax invoice number
        packing_lists = PackingList.query.filter(PackingList.id.in_(packing_list_ids)).all()
        
        for packing_list in packing_lists:
            packing_list.tax_invoice_number = tax_invoice_number
        
        db.session.commit()
        
        action_desc = f"{'Removed' if tax_invoice_number is None else 'Assigned'} tax invoice number '{tax_invoice_number}' to packing lists: {packing_list_ids}."
        
        return jsonify({
            'success': True,
            'message': action_desc,
            'packing_list_ids': packing_list_ids,
            'tax_invoice_number': tax_invoice_number
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def format_ddmmyy(date_obj):
    """Format date as DD/MM/YY"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S').date()
            except:
                return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%d/%m/%y')
    return str(date_obj)

def generate_packing_list_pdf_old(packing_list_id, show_garment_cost=False):
    """Generate PDF for packing list - OLD VERSION (BACKUP)"""
    try:
        # Get packing list details
        packing_list = PackingList.query.get(packing_list_id)
        if not packing_list:
            raise Exception("Packing list not found")
        
        # Get all stitching records in this packing list with fabric details
        lines = []
        for line in packing_list.packing_list_lines:
            if line.stitching_invoice:
                stitching = line.stitching_invoice
                line_data = {
                    'id': stitching.id,
                    'stitching_invoice_number': stitching.stitching_invoice_number,
                    'stitched_item': stitching.stitched_item,
                    'size_qty_json': stitching.size_qty_json,
                    'price': stitching.price,
                    'add_vat': stitching.add_vat,
                    'yard_consumed': stitching.yard_consumed,
                    'image_id': stitching.image_id,
                    'color': stitching.invoice_line.color if stitching.invoice_line else None,
                    'fabric_name': stitching.invoice_line.item_name if stitching.invoice_line else None,
                    'fabric_unit_price': stitching.invoice_line.unit_price if stitching.invoice_line else None,
                }
                lines.append(line_data)
        
        # Fetch image paths for all image_ids
        image_map = {}
        image_ids = [line['image_id'] for line in lines if line.get('image_id')]
        if image_ids:
            images = Image.query.filter(Image.id.in_(image_ids)).all()
            for image in images:
                # Use the best available image path (Google Drive preferred)
                image_path = image.get_image_path_for_pdf()
                if image_path:
                    image_map[image.id] = image_path
        
        # Generate PDF
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        
        # Professional Company Header
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "M.S.K Textile Trading", ln=1, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, "Professional Garment Manufacturing & Trading", ln=1, align='C')
        pdf.ln(5)
        
        # Packing List Header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, "PACKING LIST", ln=1, align='C')
        pdf.ln(2)
        
        # Header Information
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Packing List #:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, packing_list.packing_list_serial, 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Date:", 0)
        pdf.set_font("Arial", '', 10)
        # Use delivery_date if available, otherwise fall back to created_at
        display_date = packing_list.delivery_date or packing_list.created_at.date()
        pdf.cell(50, 6, format_ddmmyy(display_date), ln=1)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Customer:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, packing_list.customer.short_name if packing_list.customer else '', 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Total SKU:", 0)
        pdf.set_font("Arial", '', 10)
        pdf.cell(60, 6, str(len(lines)), 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 6, "Total Quantity:", 0)
        pdf.set_font("Arial", '', 10)
        total_qty_delivered = 0
        for line in lines:
            try:
                size_qty = json.loads(line.get('size_qty_json', '{}'))
                total_qty_delivered += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            except:
                pass
        pdf.cell(50, 6, str(total_qty_delivered), ln=1)
        
        # Comments Section
        if packing_list.comments:
            pdf.ln(3)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, "Comments:", ln=1)
            pdf.set_font("Arial", '', 9)
            # Wrap comments to fit page width
            comment_lines = []
            words = packing_list.comments.split()
            current_line = ""
            for word in words:
                if pdf.get_string_width(current_line + " " + word) < 180:  # Page width minus margins
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        comment_lines.append(current_line)
                    current_line = word
            if current_line:
                comment_lines.append(current_line)
            
            for line in comment_lines:
                pdf.cell(0, 5, line, ln=1)
        
        pdf.ln(5)
        
        # Table Header
        pdf.set_font("Arial", 'B', 8)
        col_widths = [22, 16, 25, 20, 12, 12, 12, 12, 12, 12, 15, 12]
        if show_garment_cost:
            col_widths.append(20)  # Add column for garment cost
        
        # Adjust column widths to fit page
        total_width = sum(col_widths)
        if total_width > 190:  # Page width minus margins
            scale_factor = 190 / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        headers = ["Serial #", "Image", "Garment", "Fabric", "Color", "S", "M", "L", "XL", "XXL", "XXXL", "Total"]
        if show_garment_cost:
            headers.append("Cost (Inc Vat)")
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 6, header, 1, 0, 'C')
        pdf.ln()
        
        # Table Content
        pdf.set_font("Arial", '', 7)
        for line_idx, line in enumerate(lines):
            # Serial #
            pdf.cell(col_widths[0], 18, str(line['stitching_invoice_number'] or ''), 1, 0, 'C')
            
            # Image
            img_path = image_map.get(line.get('image_id'))
            x = pdf.get_x()
            y = pdf.get_y()
            if img_path and os.path.exists(img_path):
                pdf.cell(col_widths[1], 18, '', 1, 0)
                pdf.image(img_path, x+1, y+1, col_widths[1]-2, 16)
            else:
                pdf.cell(col_widths[1], 18, '', 1, 0)
            pdf.set_xy(x+col_widths[1], y)
            
            # Garment
            pdf.cell(col_widths[2], 18, str(line['stitched_item'] or ''), 1, 0, 'C')
            
            # Fabric
            pdf.cell(col_widths[3], 18, str(line['fabric_name'] or ''), 1, 0, 'C')
            
            # Color
            pdf.cell(col_widths[4], 18, str(line['color'] or ''), 1, 0, 'C')
            
            # Size quantities
            try:
                size_qty = json.loads(line['size_qty_json']) if line['size_qty_json'] else {}
            except Exception:
                size_qty = {}
            
            for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                pdf.cell(col_widths[5 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)], 18, str(size_qty.get(sz, 0)), 1, 0, 'C')
            
            # Total quantity
            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            pdf.cell(col_widths[11], 18, str(total_qty), 1, 0, 'C')
            
            # Garment cost (if enabled)
            if show_garment_cost:
                if total_qty > 0:
                    # Calculate garment cost per piece
                    cost_per_garment = calculate_garment_cost_per_piece(line, total_qty)
                    cost_text = f"{cost_per_garment:.2f}"
                    pdf.cell(col_widths[12], 18, cost_text, 1, 0, 'C')
                else:
                    pdf.cell(col_widths[12], 18, "0.00", 1, 0, 'C')
            
            pdf.ln(18)
            
            # Add cost breakdown under each line if garment cost is enabled
            if show_garment_cost and total_qty > 0:
                add_cost_breakdown_to_pdf(pdf, line, total_qty)
        
        # Footer - only show if there are no cost breakdowns to avoid redundancy
        if not show_garment_cost:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, f"Total Quantity Delivered: {total_qty_delivered}", ln=1)
        
        # Save PDF
        safe_serial = packing_list.packing_list_serial.replace('/', '_')
        dir_path = os.path.join('packing_lists', safe_serial)
        os.makedirs(dir_path, exist_ok=True)
        pdf_name = f"{packing_list.packing_list_serial}.pdf"
        if show_garment_cost:
            pdf_name = f"{packing_list.packing_list_serial}_with_cost.pdf"
        out_path = os.path.join(dir_path, pdf_name)
        pdf.output(out_path)
        
        return out_path
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

def generate_packing_list_pdf(packing_list_id, show_garment_cost=False):
    """Generate PDF for packing list - APPLE MINIMAL BLACK & WHITE 2-COLUMN DESIGN"""
    try:
        # Get packing list details
        packing_list = PackingList.query.get(packing_list_id)
        if not packing_list:
            raise Exception("Packing list not found")
        
        # Get all stitching records in this packing list with fabric details
        lines = []
        for line in packing_list.packing_list_lines:
            if line.stitching_invoice:
                stitching = line.stitching_invoice
                line_data = {
                    'id': stitching.id,
                    'stitching_invoice_number': stitching.stitching_invoice_number,
                    'stitched_item': stitching.stitched_item,
                    'size_qty_json': stitching.size_qty_json,
                    'price': stitching.price,
                    'add_vat': stitching.add_vat,
                    'yard_consumed': stitching.yard_consumed,
                    'image_id': stitching.image_id,
                    'color': stitching.invoice_line.color if stitching.invoice_line else None,
                    'fabric_name': stitching.invoice_line.item_name if stitching.invoice_line else None,
                    'fabric_unit_price': stitching.invoice_line.unit_price if stitching.invoice_line else None,
                }
                lines.append(line_data)
        
        # Fetch image paths for all image_ids
        image_map = {}
        image_ids = [line['image_id'] for line in lines if line.get('image_id')]
        if image_ids:
            images = Image.query.filter(Image.id.in_(image_ids)).all()
            for image in images:
                image_path = image.get_image_path_for_pdf()
                if image_path:
                    image_map[image.id] = image_path
        
        # Generate PDF in LANDSCAPE for 2-column layout
        pdf = FPDF('L', 'mm', 'A4')
        pdf.add_page()
        
        # Apple minimal black & white color scheme
        black = (0, 0, 0)
        white = (255, 255, 255)
        light_gray = (245, 245, 245)
        dark_gray = (64, 64, 64)
        medium_gray = (128, 128, 128)
        
        # Ultra-minimal header (minimal space)
        pdf.set_fill_color(*white)
        pdf.rect(0, 0, 297, 12, 'F')
        
        # Company name with minimal typography
        pdf.set_text_color(*black)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_xy(0, 2)
        pdf.cell(297, 4, "M.S.K TEXTILE TRADING", ln=0, align='C')
        
        # Subtitle (minimal)
        pdf.set_font("Arial", '', 6)
        pdf.set_xy(0, 7)
        pdf.cell(297, 3, "Professional Garment Manufacturing & Trading", ln=0, align='C')
        

        
        # Minimal document title
        pdf.set_fill_color(*black)
        pdf.rect(5, 15, 287, 6, 'F')
        pdf.set_text_color(*white)
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        pdf.set_xy(5, 17)
        pdf.cell(287, 3, "PACKING LIST", ln=0, align='C')
        
        # Ultra-compact info bar (minimal space)
        pdf.set_fill_color(*light_gray)
        pdf.rect(5, 25, 287, 6, 'F')
        pdf.set_text_color(*black)
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        
        # Minimal info layout
        pdf.set_xy(10, 27)
        pdf.cell(12, 2, "PL#:", 0)
        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)
        pdf.cell(25, 2, packing_list.packing_list_serial, 0)
        
        # Date column removed as requested
        
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        pdf.cell(15, 2, "Customer:", 0)
        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)
        customer_name = packing_list.customer.short_name if packing_list.customer else 'N/A'
        pdf.cell(35, 2, customer_name, 0)
        
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        pdf.cell(12, 2, "SKU:", 0)
        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)
        pdf.cell(12, 2, str(len(lines)), 0)
        
        # Calculate total quantity
        total_qty_delivered = 0
        for line in lines:
            try:
                size_qty = json.loads(line.get('size_qty_json', '{}'))
                total_qty_delivered += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            except:
                pass
        
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        pdf.cell(18, 2, "Total Pieces:", 0)
        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)
        pdf.cell(12, 2, str(total_qty_delivered), 0)
        
        # Comments section (if any) - minimal
        if packing_list.comments:
            pdf.set_xy(10, 33)
            pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
            pdf.cell(12, 2, "Notes:", 0)
            pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)
            comment_text = packing_list.comments[:50] + "..." if len(packing_list.comments) > 50 else packing_list.comments
            pdf.cell(270, 2, comment_text, 0)
        
        # 2-COLUMN LAYOUT DESIGN
        table_start_y = 37 if packing_list.comments else 35
        
        # Split the page into 2 columns - reduced margins for more space
        left_column_x = 5
        right_column_x = 151  # Half of 297mm - 5mm margin
        column_width = 141  # (297 - 15) / 2 = 141, more space for content
        
        # Column headers for both sides - optimized size column names to save space
        headers = ["Image", "Garment", "Fabric / Serial", "Color", "S", "M", "L", "XL", "2XL", "3XL", "Total Pieces"]
        
        # Column widths for compact layout - increased image size, reduced gaps, optimized size column names
        col_widths = [18, 20, 32, 12, 5, 5, 5, 5, 5, 5, 14]  # Increased Total Pieces column width to 14, reduced Garment from 22 to 20
        if show_garment_cost:
            col_widths.append(15)  # Add cost column
            headers.append("Cost")
        
        # Adjust to fit column width
        total_width = sum(col_widths)
        if total_width > column_width:
            scale_factor = column_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        # Draw both column headers
        for col_idx, col_x in enumerate([left_column_x, right_column_x]):
            # Header background
            pdf.set_fill_color(*dark_gray)
            pdf.rect(col_x, table_start_y, column_width, 4, 'F')
            pdf.set_text_color(*white)
            pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
            
            # Header text
            x_pos = col_x
            for i, header in enumerate(headers):
                pdf.set_xy(x_pos, table_start_y + 1)
                pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
                x_pos += col_widths[i]
        
        # Table content with 2-column layout
        pdf.set_text_color(*black)
        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7) FOR ALL LINE ITEMS
        
        # Pagination logic: max 10 items per page
        max_items_per_page = 10
        total_pages = (len(lines) + max_items_per_page - 1) // max_items_per_page

        
        # Process each page
        for page_num in range(total_pages):
            if page_num > 0:
                pdf.add_page()  # Add new page (no header for continuation pages)
                
                # Add table headers on continuation pages
                for col_idx, col_x in enumerate([left_column_x, right_column_x]):
                    # Header background
                    pdf.set_fill_color(*dark_gray)
                    pdf.rect(col_x, 10, column_width, 4, 'F')  # Start at y=10 instead of table_start_y
                    pdf.set_text_color(*white)
                    pdf.set_font("Arial", 'B', 7)
                    
                    # Header text
                    x_pos = col_x
                    for i, header in enumerate(headers):
                        pdf.set_xy(x_pos, 11)  # y=11 for text positioning
                        pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
                        x_pos += col_widths[i]
                
                # Adjust table_start_y for continuation pages
                continuation_table_start_y = 14  # Start content right after headers
            else:
                continuation_table_start_y = table_start_y
            
            # Reset text formatting for content rendering
            pdf.set_text_color(*black)
            pdf.set_font("Arial", '', 7)
            
            # Calculate items for this page
            start_idx = page_num * max_items_per_page
            end_idx = min(start_idx + max_items_per_page, len(lines))
            page_lines = lines[start_idx:end_idx]

            
            # Split page lines into 2 columns
            lines_per_column = (len(page_lines) + 1) // 2
            
            # Dynamic row spacing for this page
            available_height = 160
            max_rows = max(lines_per_column, len(page_lines) - lines_per_column) if len(page_lines) > 0 else 1
            row_spacing = min(28, max(18, available_height // max_rows)) if max_rows > 0 else 28
            
            for line_idx, line in enumerate(page_lines):
                # Determine which column this line goes in
                if line_idx < lines_per_column:
                    col_x = left_column_x
                    row_y = continuation_table_start_y + 4 + (line_idx * row_spacing)
                else:
                    col_x = right_column_x
                    row_y = continuation_table_start_y + 4 + ((line_idx - lines_per_column) * row_spacing)

                # All rows white background
                pdf.set_fill_color(*white)

                pdf.rect(col_x, row_y, column_width, 26, 'F')  # Increased height to accommodate cost breakdown (22->26)

                # Add minimal border
                pdf.set_draw_color(200, 200, 200)
                pdf.rect(col_x, row_y, column_width, 26, 'D')  # Increased height to accommodate cost breakdown (22->26)
                
                x_pos = col_x
                
                # Image (10% wider and 5% longer than old layout for better visibility)
                img_path = image_map.get(line.get('image_id'))
                if img_path and os.path.exists(img_path):
                    try:
                        # Calculate 10% wider and 5% longer: 16px * 1.1 = 17.6px width, 16px * 1.05 = 16.8px height
                        img_width = round((col_widths[0] - 2) * 1.1)  # 10% wider
                        img_height = round(16 * 1.05)  # 5% longer (16.8px rounded to 17px)
                        pdf.image(img_path, x_pos + 1, row_y + 1, img_width, img_height)
                    except:
                        pass
                x_pos += col_widths[0]
                
                # Garment name
                pdf.set_xy(x_pos + 1, row_y + 1)
                garment_text = str(line['stitched_item'] or '')
                if len(garment_text) > 15:
                    garment_text = garment_text[:12] + "..."
                pdf.cell(col_widths[1] - 2, 16, garment_text, 0, 0, 'C')
                x_pos += col_widths[1]
                
                # Fabric/Serial - COMBINED COLUMN
                pdf.set_xy(x_pos + 1, row_y + 1)
                fabric_text = str(line['fabric_name'] or '')
                if len(fabric_text) > 25:
                    fabric_text = fabric_text[:22] + "..."
                pdf.cell(col_widths[2] - 2, 8, fabric_text, 0, 0, 'C')

                # Add secondary fabrics below primary fabric but above serial (10% smaller, italic)
                stitching = StitchingInvoice.query.get(line['id'])
                secondary_fabrics = []
                if stitching and stitching.garment_fabrics:
                    for garment_fabric in stitching.garment_fabrics:
                        if garment_fabric.invoice_line:
                            fabric_name = garment_fabric.invoice_line.item_name or ''
                            if fabric_name:
                                secondary_fabrics.append(fabric_name)

                # Serial number below secondary fabrics
                serial_y = row_y + 9
                if secondary_fabrics:
                    # Display secondary fabrics below primary fabric
                    pdf.set_font("Arial", 'I', 6.3)  # 10% smaller than 7, italic
                    for i, secondary_fabric in enumerate(secondary_fabrics):
                        pdf.set_xy(x_pos + 1, row_y + 9 + (i * 3))
                        if len(secondary_fabric) > 25:
                            secondary_fabric = secondary_fabric[:22] + "..."
                        pdf.cell(col_widths[2] - 2, 3, secondary_fabric, 0, 0, 'C')
                    serial_y = row_y + 9 + (len(secondary_fabrics) * 3) + 1  # Position serial after secondary fabrics

                # Reset font and display serial number
                pdf.set_font("Arial", '', 7)
                serial_text = str(line['stitching_invoice_number'] or '')
                pdf.set_xy(x_pos + 1, serial_y)
                pdf.cell(col_widths[2] - 2, 8, serial_text, 0, 0, 'C')
                x_pos += col_widths[2]
                
                # Primary color - positioned at top of cell to align with primary fabric
                pdf.set_xy(x_pos + 1, row_y + 1)
                color_text = str(line['color'] or '')
                if len(color_text) > 10:
                    color_text = color_text[:7] + "..."
                pdf.cell(col_widths[3] - 2, 8, color_text, 0, 0, 'C')

                # Add secondary fabric colors aligned with secondary fabric names
                if stitching and stitching.garment_fabrics:
                    secondary_colors = []
                    for garment_fabric in stitching.garment_fabrics:
                        if garment_fabric.invoice_line:
                            color = garment_fabric.invoice_line.color or ''
                            if color:
                                secondary_colors.append(color)

                    if secondary_colors:
                        pdf.set_font("Arial", 'I', 6.3)  # 10% smaller than 7, italic
                        for i, secondary_color in enumerate(secondary_colors):
                            # Align with secondary fabric name positioning
                            pdf.set_xy(x_pos + 1, row_y + 9 + (i * 3))
                            if len(secondary_color) > 10:
                                secondary_color = secondary_color[:7] + "..."
                            pdf.cell(col_widths[3] - 2, 3, secondary_color, 0, 0, 'C')
                        pdf.set_font("Arial", '', 7)  # Reset font

                x_pos += col_widths[3]
                
                # Size quantities - ALL VISIBLE in separate columns
                try:
                    size_qty = json.loads(line['size_qty_json']) if line['size_qty_json'] else {}
                except Exception:
                    size_qty = {}
                
                # Individual size columns for complete visibility - align with primary fabric at top
                for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                    qty = size_qty.get(sz, 0)
                    pdf.set_xy(x_pos + 1, row_y + 1)
                    pdf.cell(col_widths[4 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)] - 2, 8, str(qty), 0, 0, 'C')
                    x_pos += col_widths[4 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)]

                # Total quantity - SAME FONT SIZE - align with primary fabric at top
                total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])  # Size names unchanged in data, only display names changed
                pdf.set_xy(x_pos + 1, row_y + 1)
                pdf.set_font("Arial", 'B', 7)  # Bold but same size (increased from 6 to 7)
                pdf.cell(col_widths[10] - 2, 8, str(total_qty), 0, 0, 'C')
                pdf.set_font("Arial", '', 7)  # Reset to normal weight but same size (increased from 6 to 7)
                x_pos += col_widths[10]
                
                # Cost column (if enabled) - align with primary fabric at top
                if show_garment_cost and total_qty > 0:
                    cost_per_garment = calculate_garment_cost_per_piece(line, total_qty)
                    cost_text = f"{cost_per_garment:.2f}"
                    pdf.set_xy(x_pos + 1, row_y + 1)
                    pdf.cell(col_widths[11] - 2, 8, cost_text, 0, 0, 'C')
                    x_pos += col_widths[11]
                
                # Add horizontal cost breakdown if enabled (below the row)
                if show_garment_cost and total_qty > 0:
                    add_cost_breakdown_minimal_horizontal(pdf, line, total_qty, row_y, col_x, column_width)
            
            # Footer removed as requested
        
        # Save PDF
        safe_serial = packing_list.packing_list_serial.replace('/', '_')
        dir_path = os.path.join('packing_lists', safe_serial)
        os.makedirs(dir_path, exist_ok=True)
        pdf_name = f"{packing_list.packing_list_serial}.pdf"
        if show_garment_cost:
            pdf_name = f"{packing_list.packing_list_serial}_with_cost.pdf"
        out_path = os.path.join(dir_path, pdf_name)
        pdf.output(out_path)
        
        return out_path
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

def calculate_garment_cost_per_piece(line, total_qty):
    """Calculate garment cost per piece including all fabrics and sewing"""
    # Main fabric cost
    main_fabric_cost = 0
    if line.get('yard_consumed') and line.get('fabric_unit_price'):
        main_fabric_cost = float(line['yard_consumed']) * float(line['fabric_unit_price'])
    
    # Get multi-fabric costs
    multi_fabric_cost = 0
    stitching = StitchingInvoice.query.get(line['id'])
    if stitching:
        multi_fabric_cost = sum(float(fabric.total_fabric_cost or 0) for fabric in stitching.garment_fabrics)
        
        # Get lining costs
        lining_cost = sum(float(lining.total_cost or 0) for lining in stitching.lining_fabrics)
    else:
        lining_cost = 0
    
    # Total fabric cost
    total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
    fabric_cost_per_garment = total_fabric_cost / total_qty
    
    # Sewing cost with VAT if applicable
    sewing_price = float(line.get('price', 0))
    if line.get('add_vat'):
        sewing_cost_per_garment = sewing_price * 1.07
    else:
        sewing_cost_per_garment = sewing_price
    
    return fabric_cost_per_garment + sewing_cost_per_garment

def add_cost_breakdown_to_pdf(pdf, line, total_qty):
    """Add detailed cost breakdown to PDF"""
    stitching = StitchingInvoice.query.get(line['id'])
    if not stitching:
        return
    
    # Get all fabric costs
    main_fabric_used = float(line.get('yard_consumed', 0))
    main_fabric_price = float(line.get('fabric_unit_price', 0))
    main_fabric_cost = main_fabric_used * main_fabric_price
    
    # Get multi-fabric costs
    multi_fabric_cost = 0
    multi_fabrics_list = []
    for fabric in stitching.garment_fabrics:
        multi_fabric_cost += float(fabric.total_fabric_cost or 0)
        multi_fabrics_list.append(fabric)
    
    # Get lining fabric costs
    lining_cost = 0
    lining_fabrics_list = []
    for lining in stitching.lining_fabrics:
        lining_cost += float(lining.total_cost or 0)
        lining_fabrics_list.append(lining)
    
    # Calculate total fabric cost
    total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
    fabric_cost_per_garment = total_fabric_cost / total_qty
    
    # Calculate sewing cost with VAT if applicable
    sewing_price = float(line.get('price', 0))
    if line.get('add_vat'):
        base_sewing_cost = sewing_price
        vat_amount = base_sewing_cost * 0.07
        sewing_cost_per_garment = base_sewing_cost + vat_amount
    else:
        sewing_cost_per_garment = sewing_price
    
    total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
    
    thb_str = "THB "
    thb = thb_str
    
    # Compact cost breakdown text
    pdf.set_font("Arial", '', 5)
    pdf.cell(0, 3, f"Cost Breakdown for {line['stitched_item']}:", ln=1)
    
    # Main fabric breakdown
    if main_fabric_used > 0 and main_fabric_price > 0:
        yards_per_piece = main_fabric_used/total_qty
        cost_per_piece = main_fabric_cost/total_qty
        pdf.cell(0, 2, f"  Main: {line.get('fabric_name', '')} ({line.get('color', '')}) - {main_fabric_used:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{main_fabric_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
    
    # Multi-fabric breakdown
    if multi_fabrics_list:
        for fabric in multi_fabrics_list:
            consumption = float(fabric.consumption_yards or 0)
            unit_price = float(fabric.unit_price or 0)
            total_cost = float(fabric.total_fabric_cost or 0)
            if consumption > 0 and total_cost > 0:
                yards_per_piece = consumption/total_qty
                cost_per_piece = total_cost/total_qty
                fabric_name = fabric.invoice_line.item_name if fabric.invoice_line else 'Unknown'
                color = fabric.invoice_line.color if fabric.invoice_line else ''
                pdf.cell(0, 2, f"  Add: {fabric_name} ({color}) - {consumption:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{unit_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
    
    # Lining fabric breakdown
    if lining_fabrics_list:
        for lining in lining_fabrics_list:
            consumption = float(lining.consumption_yards or 0)
            unit_price = float(lining.unit_price or 0)
            total_cost = float(lining.total_cost or 0)
            if consumption > 0 and total_cost > 0:
                yards_per_piece = consumption/total_qty
                cost_per_piece = total_cost/total_qty
                pdf.cell(0, 2, f"  Lining: {lining.lining_name} - {consumption:.1f}yd ÷ {total_qty}pc = {yards_per_piece:.2f}yd/pc × {thb}{unit_price:.2f} = {thb}{cost_per_piece:.2f}/pc", ln=1)
    
    # Summary
    pdf.cell(0, 2, f"  Fabric Total: {thb}{fabric_cost_per_garment:.2f}/pc", ln=1)
    
    # Stitching cost
    if line.get('add_vat'):
        base_sewing_cost = sewing_price
        vat_amount = base_sewing_cost * 0.07
        total_sewing_cost = base_sewing_cost + vat_amount
        pdf.cell(0, 2, f"  Stitching: {thb}{base_sewing_cost:.2f} + {thb}{vat_amount:.2f} VAT = {thb}{total_sewing_cost:.2f}/pc", ln=1)
    else:
        pdf.cell(0, 2, f"  Stitching: {thb}{sewing_price:.2f}/pc", ln=1)
    
    pdf.cell(0, 2, f"  Total: {thb}{total_cost_per_garment:.2f}/pc", ln=1)
    pdf.ln(1)

def add_cost_breakdown_modern(pdf, line, total_qty, start_y):
    """Add modern cost breakdown to PDF"""
    stitching = StitchingInvoice.query.get(line['id'])
    if not stitching:
        return
    
    # Get all fabric costs
    main_fabric_used = float(line.get('yard_consumed', 0))
    main_fabric_price = float(line.get('fabric_unit_price', 0))
    main_fabric_cost = main_fabric_used * main_fabric_price
    
    # Get multi-fabric costs
    multi_fabric_cost = 0
    multi_fabrics_list = []
    for fabric in stitching.garment_fabrics:
        multi_fabric_cost += float(fabric.total_fabric_cost or 0)
        multi_fabrics_list.append(fabric)
    
    # Get lining fabric costs
    lining_cost = 0
    lining_fabrics_list = []
    for lining in stitching.lining_fabrics:
        lining_cost += float(lining.total_cost or 0)
        lining_fabrics_list.append(lining)
    
    # Calculate total fabric cost
    total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
    fabric_cost_per_garment = total_fabric_cost / total_qty
    
    # Calculate sewing cost with VAT if applicable
    sewing_price = float(line.get('price', 0))
    if line.get('add_vat'):
        base_sewing_cost = sewing_price
        vat_amount = base_sewing_cost * 0.07
        sewing_cost_per_garment = base_sewing_cost + vat_amount
    else:
        sewing_cost_per_garment = sewing_price
    
    total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
    
    # Modern cost breakdown card
    pdf.set_fill_color(248, 249, 250)  # Very light gray
    pdf.rect(25, start_y, 160, 20, 'F')
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(25, start_y, 160, 20, 'D')
    
    # Cost breakdown header
    pdf.set_font("Arial", 'B', 6)  # Consistent font size
    pdf.set_text_color(52, 73, 94)  # Dark slate
    pdf.set_xy(30, start_y + 2)
    pdf.cell(150, 4, f"Cost Breakdown: {line['stitched_item']}", ln=1)
    
    pdf.set_font("Arial", '', 6)
    pdf.set_text_color(0, 0, 0)
    
    # Compact cost display
    cost_text = f"Fabric: THB {fabric_cost_per_garment:.2f} | Stitching: THB {sewing_cost_per_garment:.2f} | Total: THB {total_cost_per_garment:.2f}"
    
    pdf.set_xy(30, start_y + 8)
    pdf.cell(150, 3, cost_text, ln=1)
    
    # Additional details if space allows
    if main_fabric_used > 0 and main_fabric_price > 0:
        yards_per_piece = main_fabric_used/total_qty
        pdf.set_xy(30, start_y + 12)
        pdf.cell(150, 3, f"Main: {line.get('fabric_name', '')} - {yards_per_piece:.2f}yd/pc × THB {main_fabric_price:.2f}", ln=1)
    
    if multi_fabrics_list or lining_fabrics_list:
        pdf.set_xy(30, start_y + 16)
        additional_text = ""
        if multi_fabrics_list:
            additional_text += f"Add: {len(multi_fabrics_list)} fabrics "
        if lining_fabrics_list:
            additional_text += f"Lining: {len(lining_fabrics_list)} items"
        pdf.cell(150, 3, additional_text, ln=1)

def add_cost_breakdown_apple(pdf, line, total_qty, start_y):
    """Add Apple-style cost breakdown to PDF - Customer-friendly Thai language"""
    try:
        # Calculate costs
        fabric_cost_per_garment = 0
        sewing_cost_per_garment = 0
        
        if line.get('fabric_unit_price') and line.get('yard_consumed'):
            fabric_cost_per_garment = (line['fabric_unit_price'] * line['yard_consumed']) / total_qty
        
        if line.get('price'):
            sewing_cost_per_garment = line['price']
        
        total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
        
        # Apple-style cost breakdown with Thai language
        apple_light_gray = (248, 248, 248)
        apple_dark_gray = (58, 58, 60)
        
        pdf.set_fill_color(*apple_light_gray)
        pdf.rect(20, start_y, 257, 12, 'F')
        pdf.set_draw_color(230, 230, 230)
        pdf.rect(20, start_y, 257, 12, 'D')
        
        pdf.set_text_color(*apple_dark_gray)
        pdf.set_font("Arial", 'B', 6)  # Consistent font size
        pdf.set_xy(25, start_y + 2)
        pdf.cell(247, 3, "COST BREAKDOWN:", ln=1)
        
        pdf.set_font("Arial", '', 6)  # Consistent font size
        pdf.set_xy(25, start_y + 6)
        
        # Customer-friendly cost breakdown
        cost_text = f"Fabric: {fabric_cost_per_garment:.2f} THB | Sewing: {sewing_cost_per_garment:.2f} THB | Total: {total_cost_per_garment:.2f} THB"
        pdf.cell(247, 3, cost_text, ln=1)
        
        # Additional details if available
        if line.get('yard_consumed'):
            pdf.set_xy(25, start_y + 9)
            detail_text = f"Fabric Used: {line['yard_consumed']:.2f} yards"
            pdf.cell(247, 3, detail_text, ln=1)
        
    except Exception as e:
        print(f"Error in Apple cost breakdown: {str(e)}")

def add_cost_breakdown_apple_right(pdf, line, total_qty, row_y, page_width):
    """Add Apple-style detailed cost breakdown to PDF on the right side of each line"""
    try:
        # Get stitching details for comprehensive cost calculation
        stitching = StitchingInvoice.query.get(line['id'])
        if not stitching:
            return
        
        # Get all fabric costs
        main_fabric_used = float(line.get('yard_consumed', 0))
        main_fabric_price = float(line.get('fabric_unit_price', 0))
        main_fabric_cost = main_fabric_used * main_fabric_price
        
        # Get multi-fabric costs
        multi_fabric_cost = 0
        multi_fabrics_list = []
        for fabric in stitching.garment_fabrics:
            multi_fabric_cost += float(fabric.total_fabric_cost or 0)
            multi_fabrics_list.append(fabric)
        
        # Get lining fabric costs
        lining_cost = 0
        lining_fabrics_list = []
        for lining in stitching.lining_fabrics:
            lining_cost += float(lining.total_cost or 0)
            lining_fabrics_list.append(lining)
        
        # Calculate total fabric cost
        total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
        fabric_cost_per_garment = total_fabric_cost / total_qty
        
        # Calculate sewing cost with VAT if applicable
        sewing_price = float(line.get('price', 0))
        if line.get('add_vat'):
            base_sewing_cost = sewing_price
            vat_amount = base_sewing_cost * 0.07
            sewing_cost_per_garment = base_sewing_cost + vat_amount
        else:
            sewing_cost_per_garment = sewing_price
        
        total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
        
        # Apple-style cost breakdown on the right side
        apple_light_gray = (248, 248, 248)
        apple_dark_gray = (58, 58, 60)
        
        # Position the cost breakdown on the right side - make it wider for detailed info
        breakdown_width = 120  # Wider for detailed breakdown
        breakdown_x = page_width - breakdown_width - 10  # 10px margin from right edge
        
        # Create a subtle background for the cost breakdown
        pdf.set_fill_color(*apple_light_gray)
        pdf.rect(breakdown_x, row_y, breakdown_width, 8, 'F')
        pdf.set_draw_color(230, 230, 230)
        pdf.rect(breakdown_x, row_y, breakdown_width, 8, 'D')
        
        pdf.set_text_color(*apple_dark_gray)
        pdf.set_font("Arial", 'B', 4)
        pdf.set_xy(breakdown_x + 2, row_y + 1)
        pdf.cell(breakdown_width - 4, 2, "COST BREAKDOWN:", ln=1)
        
        pdf.set_font("Arial", '', 4)
        pdf.set_xy(breakdown_x + 2, row_y + 3)
        
        # Detailed cost display
        if main_fabric_used > 0 and main_fabric_price > 0:
            yards_per_piece = main_fabric_used/total_qty
            cost_text = f"Fabric: {yards_per_piece:.2f}yd×{main_fabric_price:.1f}={fabric_cost_per_garment:.1f}"
        else:
            cost_text = f"Fabric: {fabric_cost_per_garment:.1f}"
        
        pdf.cell(breakdown_width - 4, 2, cost_text, ln=1)
        
        # Sewing cost with VAT info
        pdf.set_xy(breakdown_x + 2, row_y + 5)
        if line.get('add_vat'):
            vat_amount = sewing_price * 0.07
            sewing_text = f"Sew: {sewing_price:.1f}+{vat_amount:.1f}VAT={sewing_cost_per_garment:.1f}"
        else:
            sewing_text = f"Sew: {sewing_cost_per_garment:.1f}"
        pdf.cell(breakdown_width - 4, 2, sewing_text, ln=1)
        
        # Total cost
        pdf.set_xy(breakdown_x + 2, row_y + 7)
        total_text = f"Total: {total_cost_per_garment:.1f} THB"
        pdf.set_font("Arial", 'B', 4)
        pdf.cell(breakdown_width - 4, 2, total_text, ln=1)
        
    except Exception as e:
        print(f"Error in Apple right-side cost breakdown: {str(e)}")

def add_cost_breakdown_minimal_horizontal(pdf, line, total_qty, row_y, col_x, column_width):
    """Add minimal horizontal cost breakdown to PDF - compact and clear"""
    try:
        # Get stitching details for comprehensive cost calculation
        stitching = StitchingInvoice.query.get(line['id'])
        if not stitching:
            return
        
        # Get all fabric costs
        main_fabric_used = float(line.get('yard_consumed', 0))
        main_fabric_price = float(line.get('fabric_unit_price', 0))
        main_fabric_cost = main_fabric_used * main_fabric_price
        
        # Get multi-fabric costs
        multi_fabric_cost = 0
        multi_fabrics_list = []
        for fabric in stitching.garment_fabrics:
            multi_fabric_cost += float(fabric.total_fabric_cost or 0)
            multi_fabrics_list.append(fabric)
        
        # Get lining fabric costs
        lining_cost = 0
        lining_fabrics_list = []
        for lining in stitching.lining_fabrics:
            lining_cost += float(lining.total_cost or 0)
            lining_fabrics_list.append(lining)
        
        # Calculate total fabric cost
        total_fabric_cost = main_fabric_cost + multi_fabric_cost + lining_cost
        fabric_cost_per_garment = total_fabric_cost / total_qty
        
        # Calculate sewing cost with VAT if applicable
        sewing_price = float(line.get('price', 0))
        if line.get('add_vat'):
            base_sewing_cost = sewing_price
            vat_amount = base_sewing_cost * 0.07
            sewing_cost_per_garment = base_sewing_cost + vat_amount
        else:
            sewing_cost_per_garment = sewing_price
        
        total_cost_per_garment = fabric_cost_per_garment + sewing_cost_per_garment
        
        # Minimal horizontal cost breakdown
        light_gray = (245, 245, 245)
        dark_gray = (64, 64, 64)
        
        # Create a subtle background for the cost breakdown - properly aligned within row
        pdf.set_fill_color(*light_gray)
        pdf.rect(col_x, row_y + 20, column_width, 6, 'F')  # Positioned to fit within 26px row height
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(col_x, row_y + 20, column_width, 6, 'D')  # Positioned to fit within 26px row height
        
        pdf.set_text_color(*dark_gray)
        pdf.set_font("Arial", 'B', 7)  # Increased font size by 10% (6->7)
        pdf.set_xy(col_x + 2, row_y + 21)
        pdf.cell(column_width - 4, 1, "COST:", ln=0)

        pdf.set_font("Arial", '', 7)  # Increased font size by 10% (6->7)

        # Enhanced cost breakdown with detailed explanations - 2 lines
        line1_details = []
        line2_details = []

        # Line 1: Main fabric and consumption calculation
        if main_fabric_used > 0 and main_fabric_price > 0:
            yards_per_piece = main_fabric_used/total_qty
            main_fabric_cost_per_piece = main_fabric_cost/total_qty
            line1_details.append(f"Main: {yards_per_piece:.2f}yd/pc×{main_fabric_price:.1f}={main_fabric_cost_per_piece:.1f}")

        # Add secondary fabrics to line 1
        if multi_fabrics_list:
            for fabric in multi_fabrics_list:
                consumption = float(fabric.consumption_yards or 0)
                unit_price = float(fabric.unit_price or 0)
                if consumption > 0 and unit_price > 0:
                    yards_per_piece = consumption/total_qty
                    cost_per_piece = (consumption * unit_price)/total_qty
                    line1_details.append(f"Sec: {yards_per_piece:.2f}yd/pc×{unit_price:.1f}={cost_per_piece:.1f}")

        # Add lining fabrics to line 1
        if lining_fabrics_list:
            for lining in lining_fabrics_list:
                consumption = float(lining.consumption_yards or 0)
                unit_price = float(lining.unit_price or 0)
                if consumption > 0 and unit_price > 0:
                    yards_per_piece = consumption/total_qty
                    cost_per_piece = (consumption * unit_price)/total_qty
                    line1_details.append(f"Lining: {yards_per_piece:.2f}yd/pc×{unit_price:.1f}={cost_per_piece:.1f}")

        # Line 2: Sewing cost and total
        if line.get('add_vat'):
            vat_amount = sewing_price * 0.07
            line2_details.append(f"Sew: {sewing_price:.1f}+{vat_amount:.1f}VAT={sewing_cost_per_garment:.1f}")
        else:
            line2_details.append(f"Sew: {sewing_cost_per_garment:.1f}")

        line2_details.append(f"Total: {total_cost_per_garment:.1f} THB")

        # Join lines with separators
        line1_text = " | ".join(line1_details) if line1_details else f"Fabric: {fabric_cost_per_garment:.1f}"
        line2_text = " | ".join(line2_details)

        # Display on 2 lines with proper spacing within the cost breakdown box
        pdf.set_xy(col_x + 15, row_y + 21)  # Line 1: Start right after "COST:" label (updated to match box position)
        pdf.cell(column_width - 15, 1, line1_text, ln=0)  # ln=0 to not advance to next line

        pdf.set_xy(col_x + 15, row_y + 24)  # Line 2: 3px below line 1, within the 6px cost box (updated positioning)
        pdf.cell(column_width - 15, 1, line2_text, ln=1)
        
    except Exception as e:
        print(f"Error in minimal horizontal cost breakdown: {str(e)}")
