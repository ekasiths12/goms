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
        
        # Order by creation date (newest first)
        query = query.order_by(StitchingInvoiceGroup.created_at.desc())
        
        # Execute query
        group_bills = query.all()
        
        # Convert to dictionary format with detailed structure
        result = []
        for group_bill in group_bills:
            group_dict = group_bill.to_dict()
            
            # Add detailed structure for multi-level display
            details = get_group_bill_details(group_bill.id)
            group_dict['details'] = details
            
            # FIXED: Use details totals instead of model totals to include secondary fabrics
            group_dict['total_fabric_value'] = details.get('total_fabric_value', 0)
            group_dict['total_stitching_value'] = details.get('total_stitching_value', 0)
            group_dict['total_items'] = details.get('total_items', 0)
            
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
    """Generate stitching fee PDF for a group bill with packing list style - single column layout"""
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
                'image_id': stitching_invoice.image_id,
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
    
    # Fetch image paths for all image_ids
    image_map = {}
    image_ids = [line['image_id'] for line in lines if line.get('image_id')]
    if image_ids:
        from app.models.image import Image
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        for image in images:
            image_map[image.id] = image.get_image_path_for_pdf()
    
    # Fetch lining fabrics for all stitching invoices in this group
    lining_fabrics = []
    stitching_ids = [line['id'] for line in lines]
    if stitching_ids:
        from app.models.stitching import LiningFabric
        lining_fabrics = LiningFabric.query.filter(
            LiningFabric.stitching_invoice_id.in_(stitching_ids)
        ).all()
    
    # Create PDF with portrait orientation for single column
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # Apple minimal black & white color scheme (same as packing list)
    black = (0, 0, 0)
    white = (255, 255, 255)
    light_gray = (245, 245, 245)
    dark_gray = (64, 64, 64)
    medium_gray = (128, 128, 128)
    
    # Page dimensions
    page_width = 210
    page_height = 297
    margin = 5
    content_width = page_width - (2 * margin)
    
    # Ultra-minimal header (same as packing list)
    pdf.set_fill_color(*white)
    pdf.rect(0, 0, page_width, 12, 'F')
    
    # Company name with minimal typography
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_xy(0, 2)
    pdf.cell(page_width, 4, "M.S.K TEXTILE TRADING", ln=0, align='C')
    
    # Subtitle (minimal)
    pdf.set_font("Arial", '', 6)
    pdf.set_xy(0, 7)
    pdf.cell(page_width, 3, "Professional Garment Manufacturing & Trading", ln=0, align='C')
    
    # Minimal document title
    pdf.set_fill_color(*black)
    pdf.rect(margin, 15, content_width, 6, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    pdf.set_xy(margin, 17)
    pdf.cell(content_width, 3, "STITCHING INVOICE", ln=0, align='C')
    
    # Ultra-compact info bar (minimal space)
    pdf.set_fill_color(*light_gray)
    pdf.rect(margin, 25, content_width, 6, 'F')
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 7)
    
    # Minimal info layout
    pdf.set_xy(margin + 5, 27)
    pdf.cell(12, 2, "Group#:", 0)
    pdf.set_font("Arial", '', 7)
    pdf.cell(25, 2, group_bill.group_number, 0)
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(12, 2, "Date:", 0)
    pdf.set_font("Arial", '', 7)
    display_date = group_bill.invoice_date or group_bill.created_at
    pdf.cell(20, 2, format_ddmmyy(display_date), 0)
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(15, 2, "Customer:", 0)
    pdf.set_font("Arial", '', 7)
    customer_name = group_bill.customer.short_name if group_bill.customer else 'N/A'
    pdf.cell(35, 2, customer_name, 0)
    
    # Calculate total items
    total_items = 0
    for line in lines:
        size_qty = line.get('size_qty', {})
        total_items += sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(12, 2, "Items:", 0)
    pdf.set_font("Arial", '', 7)
    pdf.cell(12, 2, str(total_items), 0)
    
    # Comments section (if any) - minimal
    if group_bill.stitching_comments:
        pdf.set_xy(margin + 5, 33)
        pdf.set_font("Arial", 'B', 7)
        pdf.cell(12, 2, "Notes:", 0)
        pdf.set_font("Arial", '', 7)
        comment_text = group_bill.stitching_comments[:50] + "..." if len(group_bill.stitching_comments) > 50 else group_bill.stitching_comments
        pdf.cell(content_width - 25, 2, comment_text, 0)
    
    # SINGLE COLUMN LAYOUT DESIGN
    table_start_y = 37 if group_bill.stitching_comments else 35
    
    # Column headers - optimized for single column
    headers = ["Date", "Image", "Garment", "Fabric/Serial", "Color", "S", "M", "L", "XL", "2XL", "3XL", "Total", "Price", "Value"]
    
    # Column widths for compact single column layout
    col_widths = [15, 18, 25, 35, 15, 8, 8, 8, 8, 8, 8, 12, 15, 20]
    
    # Header background
    pdf.set_fill_color(*dark_gray)
    pdf.rect(margin, table_start_y, content_width, 4, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    
    # Header text
    x_pos = margin
    for i, header in enumerate(headers):
        pdf.set_xy(x_pos, table_start_y + 1)
        pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
        x_pos += col_widths[i]
    
    # Group lines by tax invoice number
    tax_groups = {}
    for line in lines:
        tax_inv = line.get('pl_tax_invoice_number', None)
        if tax_inv not in tax_groups:
            tax_groups[tax_inv] = []
        tax_groups[tax_inv].append(line)
    
    # Table content with proper pagination
    current_y = table_start_y + 4
    line_idx = 0
    tax_group_totals = {}
    max_y = 280  # Maximum Y position before new page (A4 height ~297mm, leave margin)
    page_row_count = 0  # Track rows on current page
    
    for tax_inv, group_lines in tax_groups.items():
        # Process each line in this tax group - no header above data
        tax_group_total = 0
        group_line_idx = 0  # Reset line index for each group
        
        for group_line in group_lines:
            # Calculate row position based on current page row count
            row_y = current_y + (page_row_count * 18)
            
            # Check if we need a new page
            if row_y + 18 > max_y:
                pdf.add_page()
                
                # Add minimal header on continuation page
                pdf.set_fill_color(*white)
                pdf.rect(0, 0, page_width, 12, 'F')
                pdf.set_text_color(*black)
                pdf.set_font("Arial", 'B', 12)
                pdf.set_xy(0, 2)
                pdf.cell(page_width, 4, "M.S.K TEXTILE TRADING", ln=0, align='C')
                pdf.set_font("Arial", '', 6)
                pdf.set_xy(0, 7)
                pdf.cell(page_width, 3, "Professional Garment Manufacturing & Trading", ln=0, align='C')
                
                # Document title
                pdf.set_fill_color(*black)
                pdf.rect(margin, 15, content_width, 6, 'F')
                pdf.set_text_color(*white)
                pdf.set_font("Arial", 'B', 7)
                pdf.set_xy(margin, 17)
                pdf.cell(content_width, 3, "STITCHING INVOICE (CONTINUED)", ln=0, align='C')
                
                # Table headers
                continuation_table_start_y = 25
                pdf.set_fill_color(*dark_gray)
                pdf.rect(margin, continuation_table_start_y, content_width, 4, 'F')
                pdf.set_text_color(*white)
                pdf.set_font("Arial", 'B', 7)
                x_pos = margin
                for i, header in enumerate(headers):
                    pdf.set_xy(x_pos, continuation_table_start_y + 1)
                    pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
                    x_pos += col_widths[i]
                
                # Reset for new page
                current_y = continuation_table_start_y + 4
                page_row_count = 0  # Reset row count for new page
                row_y = current_y  # First row on new page
                
                # Reset text formatting for content rendering
                pdf.set_text_color(*black)
                pdf.set_font("Arial", '', 7)
            
            # Row background
            if group_line_idx % 2 == 0:
                pdf.set_fill_color(*white)
            else:
                pdf.set_fill_color(*light_gray)
            pdf.rect(margin, row_y, content_width, 18, 'F')
            
            # Row border
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(margin, row_y, content_width, 18, 'D')
            
            x_pos = margin
            
            # Date
            pdf.set_text_color(*black)
            pdf.set_font("Arial", '', 7)
            pdf.set_xy(x_pos + 1, row_y + 1)
            pl_date = format_ddmmyy(group_line.get('pl_created_at')) if group_line.get('pl_created_at') else ''
            pdf.cell(col_widths[0] - 2, 16, pl_date, 0, 0, 'C')
            x_pos += col_widths[0]
            
            # Image
            img_path = image_map.get(group_line.get('image_id'))
            if img_path and os.path.exists(img_path):
                try:
                    img_width = min(16, col_widths[1] - 2)
                    img_height = min(16, 16)
                    pdf.image(img_path, x_pos + 1, row_y + 1, img_width, img_height)
                except:
                    pass
            x_pos += col_widths[1]
            
            # Garment name
            pdf.set_xy(x_pos + 1, row_y + 1)
            garment_text = str(group_line['stitched_item'] or '')
            if len(garment_text) > 20:
                garment_text = garment_text[:17] + "..."
            pdf.cell(col_widths[2] - 2, 16, garment_text, 0, 0, 'C')
            x_pos += col_widths[2]
            
            # Fabric/Serial - Two lines
            pdf.set_xy(x_pos + 1, row_y + 1)
            fabric_text = str(group_line['fabric_name'] or '')
            if len(fabric_text) > 30:
                fabric_text = fabric_text[:27] + "..."
            pdf.cell(col_widths[3] - 2, 8, fabric_text, 0, 0, 'C')

            # Add secondary fabrics below primary fabric but above serial (10% smaller, italic)
            stitching = StitchingInvoice.query.get(group_line['id'])
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
                    if len(secondary_fabric) > 30:
                        secondary_fabric = secondary_fabric[:27] + "..."
                    pdf.cell(col_widths[3] - 2, 3, secondary_fabric, 0, 0, 'C')
                serial_y = row_y + 9 + (len(secondary_fabrics) * 3) + 1  # Position serial after secondary fabrics

            # Reset font and display serial number
            pdf.set_font("Arial", '', 7)
            serial_text = str(group_line['stitching_invoice_number'] or '')
            pdf.set_xy(x_pos + 1, serial_y)
            pdf.cell(col_widths[3] - 2, 8, serial_text, 0, 0, 'C')
            x_pos += col_widths[3]
            
            # Primary color - positioned at top of cell to align with primary fabric
            pdf.set_xy(x_pos + 1, row_y + 1)
            color_text = str(group_line['color'] or '')
            if len(color_text) > 12:
                color_text = color_text[:9] + "..."
            pdf.cell(col_widths[4] - 2, 8, color_text, 0, 0, 'C')

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
                        if len(secondary_color) > 12:
                            secondary_color = secondary_color[:9] + "..."
                        pdf.cell(col_widths[4] - 2, 3, secondary_color, 0, 0, 'C')
                    pdf.set_font("Arial", '', 7)  # Reset font

            x_pos += col_widths[4]
            
            # Size quantities
            size_qty = group_line['size_qty']
            for sz in ["S", "M", "L", "XL", "XXL", "XXXL"]:
                qty = size_qty.get(sz, 0)
                pdf.set_xy(x_pos + 1, row_y + 1)
                pdf.cell(col_widths[5 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)] - 2, 8, str(qty), 0, 0, 'C')
                x_pos += col_widths[5 + ["S", "M", "L", "XL", "XXL", "XXXL"].index(sz)]

            # Total quantity - align with primary fabric at top
            total_qty = sum(size_qty.get(sz, 0) for sz in ["S", "M", "L", "XL", "XXL", "XXXL"])
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.set_font("Arial", 'B', 7)
            pdf.cell(col_widths[11] - 2, 8, str(total_qty), 0, 0, 'C')
            pdf.set_font("Arial", '', 7)
            x_pos += col_widths[11]

            # Price - align with primary fabric at top
            base_price = group_line['price']
            if group_line.get('add_vat'):
                vat_amount = base_price * 0.07
                vat_inclusive_price = base_price + vat_amount
            else:
                vat_inclusive_price = base_price
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.cell(col_widths[12] - 2, 8, f"{vat_inclusive_price:,.2f}", 0, 0, 'C')
            x_pos += col_widths[12]

            # Value - align with primary fabric at top
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.cell(col_widths[13] - 2, 8, f"{group_line['total_value']:,.2f}", 0, 0, 'C')
            
            # Add to tax group total
            tax_group_total += float(group_line['total_value'] or 0)
            group_line_idx += 1
            page_row_count += 1  # Increment page row counter
        
        # Tax group subtotal (minimal) - shows tax invoice number here
        tax_group_totals[tax_inv] = tax_group_total
        pdf.set_font("Arial", 'B', 7)
        pdf.set_text_color(*black)
        tax_total_y = current_y + (page_row_count * 18) + 1
        pdf.set_xy(margin + 5, tax_total_y)
        
        # Get packing list number for this group
        packing_list_number = ""
        for group_line in group_lines:
            if group_line.get('packing_list_serial'):
                packing_list_number = group_line['packing_list_serial']
                break
        
        pdf.cell(content_width - 10, 3, f"Total for Tax Invoice {tax_inv if tax_inv else '(None)'}: {tax_group_total:,.2f} THB - PL: {packing_list_number}", ln=0)
        
        # Move current_y to after this group for next group
        current_y = tax_total_y + 6  # After group total + 6mm gap between groups
        page_row_count += 1  # Account for the group total row
    
    # Calculate totals
    stitching_vat_total = 0
    stitching_base_total = 0
    
    for line in lines:
        if line.get('add_vat'):
            total_value = float(line['total_value'] or 0)
            base_amount = total_value / 1.07
            vat_amount = total_value - base_amount
            stitching_vat_total += vat_amount
            stitching_base_total += base_amount
        else:
            stitching_base_total += float(line['total_value'] or 0)
    
    # Calculate withholding tax
    stitching_withholding_tax = 0
    if apply_withholding_tax:
        stitching_withholding_tax = stitching_base_total * 0.03
    
    # Calculate stitching grand total
    stitching_grand_total = sum(line['total_value'] for line in lines) - stitching_withholding_tax
    
    # Summary section (minimal) - positioned after all groups with small gap
    summary_start_y = current_y + 3  # Small gap after last group total
    
    # Calculate actual height needed for stitching summary box
    title_height = 5  # "STITCHING SUMMARY" title (3mm text + 2mm gap)
    data_height = 10  # 2 lines of data (2 * 3mm + 4mm gap)
    summary_box_height = title_height + data_height  # 15mm total
    
    # Summary box (minimal) - calculated height
    summary_height = summary_box_height
    pdf.set_fill_color(*light_gray)
    pdf.rect(margin, summary_start_y, content_width, summary_height, 'F')
    pdf.set_draw_color(*dark_gray)
    pdf.rect(margin, summary_start_y, content_width, summary_height, 'D')
    
    # Summary content
    pdf.set_font("Arial", 'B', 7)
    pdf.set_text_color(*black)
    pdf.set_xy(margin + 5, summary_start_y + 2)  # Changed from +3 to +2 for 2mm gap
    pdf.cell(40, 3, "STITCHING SUMMARY", ln=0)
    
    # Line 1: Sub Total, VAT, Withholding Tax
    line1_y = summary_start_y + 6  # Changed from +7 to +6 for 2mm gap after title
    pdf.set_font("Arial", '', 7)
    pdf.set_xy(margin + 5, line1_y)
    pdf.cell(30, 3, "Sub Total:", ln=0)
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(40, 3, f"{stitching_base_total:,.2f} THB", ln=0)
    
    if stitching_vat_total > 0:
        pdf.set_font("Arial", '', 7)
        pdf.cell(30, 3, "VAT 7%:", ln=0)
        pdf.set_font("Arial", 'B', 7)
        pdf.cell(40, 3, f"{stitching_vat_total:,.2f} THB", ln=0)
    
    if apply_withholding_tax:
        pdf.set_font("Arial", '', 7)
        pdf.cell(30, 3, "WHT 3%:", ln=0)
        pdf.set_font("Arial", 'B', 7)
        pdf.cell(40, 3, f"{stitching_withholding_tax:,.2f} THB", ln=1)
    
    # Line 2: Grand Total - aligned with Sub Total
    stitching_grand_total_calc = stitching_base_total + stitching_vat_total - stitching_withholding_tax
    pdf.set_font("Arial", 'B', 7)
    pdf.set_xy(margin + 5, line1_y + 5)
    pdf.cell(30, 3, "Grand Total:", ln=0)
    pdf.cell(40, 3, f"{stitching_grand_total_calc:,.2f} THB", ln=1)
    
    # Add symmetrical gap after Grand Total (same as gap before data)
    # The gap is already built into the summary_height calculation
    
    # Lining fabrics section (if any) - truly dynamic sizing with proper spacing
    lining_total = 0
    if lining_fabrics:
        # Calculate exact height needed for lining section with proper spacing
        title_height = 5  # "LINING FABRICS" title (3mm text + 2mm gap)
        header_height = 5  # Table header row (3mm text + 2mm gap)
        row_height = 4     # Each data row (3mm text + 1mm gap)
        summary_height = 8  # Summary lines (2 lines * 3mm + 2mm gap)
        padding = 4        # Increased padding for 2mm gap top and bottom
        
        # Calculate total height needed
        total_lining_height = title_height + header_height + (len(lining_fabrics) * row_height) + summary_height + padding
        
        # Position lining box after stitching summary content ends + 5mm gap
        stitching_summary_end = summary_start_y + 15  # summary_start_y + 15mm box height
        lining_start_y = stitching_summary_end + 5  # 5mm gap after stitching summary box
        
        # Lining section box - truly dynamic sizing
        pdf.set_fill_color(*light_gray)
        pdf.rect(margin, lining_start_y, content_width, total_lining_height, 'F')
        pdf.set_draw_color(*dark_gray)
        pdf.rect(margin, lining_start_y, content_width, total_lining_height, 'D')
        
        # Lining section title
        pdf.set_xy(margin + 5, lining_start_y + 2)  # Changed from +1 to +2 for 2mm gap
        pdf.set_font("Arial", 'B', 7)
        pdf.cell(content_width - 10, 3, "LINING FABRICS", ln=0)
        
        # Lining table header
        pdf.set_font("Arial", 'B', 7)
        pdf.set_text_color(*black)
        pdf.set_xy(margin + 5, lining_start_y + 6)  # Changed from +5 to +6 for 2mm gap after title
        lining_col_widths = [25, 50, 25, 25, 30]
        
        pdf.cell(lining_col_widths[0], 3, "Serial", ln=0, align='C')
        pdf.cell(lining_col_widths[1], 3, "Lining Name", ln=0, align='C')
        pdf.cell(lining_col_widths[2], 3, "Consumption", ln=0, align='C')
        pdf.cell(lining_col_widths[3], 3, "Unit Price", ln=0, align='C')
        pdf.cell(lining_col_widths[4], 3, "Total Cost", ln=1, align='C')
        
        # Lining table content - with 1mm gap after header
        pdf.set_font("Arial", '', 7)
        for i, lf in enumerate(lining_fabrics):
            row_y = lining_start_y + 10 + (i * row_height)  # Changed from +9 to +10 for 2mm gap after header
            
            pdf.set_xy(margin + 5, row_y)
            pdf.cell(lining_col_widths[0], 3, str(lf.stitching_invoice.stitching_invoice_number or ''), ln=0, align='C')
            pdf.cell(lining_col_widths[1], 3, str(lf.lining_name or ''), ln=0, align='C')
            pdf.cell(lining_col_widths[2], 3, f"{float(lf.consumption_yards or 0):.2f} yards", ln=0, align='C')
            pdf.cell(lining_col_widths[3], 3, f"{float(lf.unit_price or 0):.2f} THB", ln=0, align='C')
            pdf.cell(lining_col_widths[4], 3, f"{float(lf.total_cost or 0):,.2f} THB", ln=1, align='C')
        
        # Calculate lining totals
        lining_total = sum(float(lf.total_cost or 0) for lf in lining_fabrics)
        
        # Lining summary
        if lining_total > 0:
            lining_summary_y = lining_start_y + 10 + (len(lining_fabrics) * row_height) + 2  # Changed from +1 to +2 for 2mm gap
            
            # Line 1: Lining Sub Total and VAT on same line - aligned with stitching summary
            pdf.set_font("Arial", '', 7)
            pdf.set_text_color(*black)
            pdf.set_xy(margin + 5, lining_summary_y)
            pdf.cell(30, 3, "Lining Sub Total:", ln=0)
            pdf.set_font("Arial", 'B', 7)
            pdf.cell(40, 3, f"{lining_total:,.2f} THB", ln=0)
            
            pdf.set_font("Arial", '', 7)
            pdf.cell(30, 3, "VAT 7%:", ln=0)
            pdf.set_font("Arial", 'B', 7)
            pdf.cell(40, 3, f"{lining_total * 0.07:,.2f} THB", ln=1)
            
            # Line 2: Lining Total - aligned with stitching summary
            lining_grand_total = lining_total * 1.07
            pdf.set_font("Arial", 'B', 7)
            pdf.set_xy(margin + 5, lining_summary_y + 5)  # Changed from 4 to 5 to match stitching summary
            pdf.cell(30, 3, "Lining Total:", ln=0)
            pdf.cell(40, 3, f"{lining_grand_total:,.2f} THB", ln=1)
    
    # Calculate final total
    if lining_total > 0:
        total_payment_due = stitching_grand_total_calc + lining_grand_total
    else:
        total_payment_due = stitching_grand_total_calc
    
    # Final total (minimal) - dynamically positioned based on actual content with light grey background
    if lining_fabrics:
        # Position after lining box ends + 5mm gap
        lining_end = lining_start_y + total_lining_height
        final_start_y = lining_end + 5  # 5mm gap after lining box
    else:
        # Position after stitching summary box + 5mm gap
        final_start_y = summary_start_y + summary_height + 5  # 5mm gap after stitching summary
    
    pdf.set_fill_color(*light_gray)
    pdf.rect(margin, final_start_y, content_width, 8, 'F')
    pdf.set_draw_color(*black)
    pdf.rect(margin, final_start_y, content_width, 8, 'D')
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_xy(margin + 5, final_start_y + 2)
    pdf.cell(content_width - 10, 4, f"TOTAL PAYMENT DUE: {total_payment_due:,.2f} THB", ln=0, align='C')
    
    # Minimal footer
    footer_y = final_start_y + 12
    pdf.set_fill_color(*black)
    pdf.rect(0, footer_y, page_width, 6, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    pdf.set_xy(0, footer_y + 2)
    pdf.cell(page_width, 3, "STITCHING INVOICE COMPLETED", ln=0, align='C')
    
    # Save PDF
    safe_group_number = group_bill.group_number.replace('/', '_').replace('\\', '_')
    group_dir = os.path.join('group_bills', safe_group_number)
    os.makedirs(group_dir, exist_ok=True)
    
    pdf_path = os.path.join(group_dir, f"{group_bill.group_number}_stitching.pdf")
    pdf.output(pdf_path)
    
    return pdf_path

def generate_fabric_used_pdf(group_id):
    """Generate fabric used PDF for a group bill with packing list style - single column layout"""
    group_bill = StitchingInvoiceGroup.query.get(group_id)
    if not group_bill:
        raise ValueError("Group bill not found")
    
    # Get all stitching records in this group with fabric information
    lines = []
    for group_line in group_bill.group_lines:
        stitching_invoice = group_line.stitching_invoice
        if stitching_invoice:
            # Primary fabric from invoice line
            if stitching_invoice.invoice_line:
                primary_fabric = {
                    'stitching_invoice_number': stitching_invoice.stitching_invoice_number,
                    'stitched_item': stitching_invoice.stitched_item,
                    'fabric_name': stitching_invoice.invoice_line.item_name,
                    'color': stitching_invoice.invoice_line.color,
                    'yards_consumed': float(stitching_invoice.yard_consumed or 0),
                    'unit_price': float(stitching_invoice.invoice_line.unit_price or 0),
                    'total_value': float(stitching_invoice.yard_consumed or 0) * float(stitching_invoice.invoice_line.unit_price or 0),
                    'fabric_tax_invoice_number': stitching_invoice.invoice_line.invoice.tax_invoice_number if stitching_invoice.invoice_line.invoice else None,
                    'fabric_invoice_number': stitching_invoice.invoice_line.invoice.invoice_number if stitching_invoice.invoice_line.invoice else None,
                    'packing_list_serial': None,
                    'pl_created_at': None,
                    'pl_tax_invoice_number': None,
                    'image_id': stitching_invoice.image_id,
                    'is_primary': True
                }
                
                # Get packing list information
                packing_list_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_invoice.id).first()
                if packing_list_line and packing_list_line.packing_list:
                    primary_fabric['packing_list_serial'] = packing_list_line.packing_list.packing_list_serial
                    primary_fabric['pl_created_at'] = packing_list_line.packing_list.created_at
                    primary_fabric['pl_tax_invoice_number'] = packing_list_line.packing_list.tax_invoice_number
                
                lines.append(primary_fabric)
            
            # Secondary fabrics from GarmentFabric model
            for garment_fabric in stitching_invoice.garment_fabrics:
                if garment_fabric.invoice_line:
                    secondary_fabric = {
                        'stitching_invoice_number': stitching_invoice.stitching_invoice_number,
                        'stitched_item': stitching_invoice.stitched_item,
                        'fabric_name': garment_fabric.invoice_line.item_name,
                        'color': garment_fabric.invoice_line.color,
                        'yards_consumed': float(garment_fabric.consumption_yards or 0),
                        'unit_price': float(garment_fabric.unit_price or 0),
                        'total_value': float(garment_fabric.total_fabric_cost or 0),
                        'fabric_tax_invoice_number': garment_fabric.invoice_line.invoice.tax_invoice_number if garment_fabric.invoice_line.invoice else None,
                        'fabric_invoice_number': garment_fabric.invoice_line.invoice.invoice_number if garment_fabric.invoice_line.invoice else None,
                        'packing_list_serial': None,
                        'pl_created_at': None,
                        'pl_tax_invoice_number': None,
                        'image_id': stitching_invoice.image_id,
                        'is_primary': False
                    }
                    
                    # Get packing list information
                    packing_list_line = PackingListLine.query.filter_by(stitching_invoice_id=stitching_invoice.id).first()
                    if packing_list_line and packing_list_line.packing_list:
                        secondary_fabric['packing_list_serial'] = packing_list_line.packing_list.packing_list_serial
                        secondary_fabric['pl_created_at'] = packing_list_line.packing_list.created_at
                        secondary_fabric['pl_tax_invoice_number'] = packing_list_line.packing_list.tax_invoice_number
                    
                    lines.append(secondary_fabric)
    
    # Fetch image paths for all image_ids
    image_map = {}
    image_ids = [line.get('image_id') for line in lines if line.get('image_id')]
    if image_ids:
        from app.models.image import Image
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        for image in images:
            image_map[image.id] = image.get_image_path_for_pdf()
    
    # Create PDF with portrait orientation for single column
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    
    # Apple minimal black & white color scheme (same as packing list)
    black = (0, 0, 0)
    white = (255, 255, 255)
    light_gray = (245, 245, 245)
    dark_gray = (64, 64, 64)
    medium_gray = (128, 128, 128)
    
    # Page dimensions
    page_width = 210
    page_height = 297
    margin = 5
    content_width = page_width - (2 * margin)
    
    # Ultra-minimal header (same as packing list)
    pdf.set_fill_color(*white)
    pdf.rect(0, 0, page_width, 12, 'F')
    
    # Company name with minimal typography
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_xy(0, 2)
    pdf.cell(page_width, 4, "BETA WEAVING FACTORY CO., LTD", ln=0, align='C')
    
    # Subtitle (minimal)
    pdf.set_font("Arial", '', 6)
    pdf.set_xy(0, 7)
    pdf.cell(page_width, 3, "Professional Garment Manufacturing & Trading", ln=0, align='C')
    
    # Minimal document title
    pdf.set_fill_color(*black)
    pdf.rect(margin, 15, content_width, 6, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    pdf.set_xy(margin, 17)
    pdf.cell(content_width, 3, "FABRIC USED INVOICE", ln=0, align='C')
    
    # Ultra-compact info bar (minimal space)
    pdf.set_fill_color(*light_gray)
    pdf.rect(margin, 25, content_width, 6, 'F')
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 7)
    
    # Minimal info layout
    pdf.set_xy(margin + 5, 27)
    pdf.cell(12, 2, "Group#:", 0)
    pdf.set_font("Arial", '', 7)
    pdf.cell(25, 2, group_bill.group_number, 0)
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(12, 2, "Date:", 0)
    pdf.set_font("Arial", '', 7)
    display_date = group_bill.invoice_date or group_bill.created_at
    pdf.cell(20, 2, format_ddmmyy(display_date), 0)
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(15, 2, "Customer:", 0)
    pdf.set_font("Arial", '', 7)
    customer_name = group_bill.customer.short_name if group_bill.customer else 'N/A'
    pdf.cell(35, 2, customer_name, 0)
    
    # Calculate total yards
    total_yards = sum(line['yards_consumed'] for line in lines)
    
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(12, 2, "Yards:", 0)
    pdf.set_font("Arial", '', 7)
    pdf.cell(12, 2, f"{total_yards:.2f}", 0)
    
    # Comments section (if any) - minimal
    if group_bill.fabric_comments:
        pdf.set_xy(margin + 5, 33)
        pdf.set_font("Arial", 'B', 7)
        pdf.cell(12, 2, "Notes:", 0)
        pdf.set_font("Arial", '', 7)
        comment_text = group_bill.fabric_comments[:50] + "..." if len(group_bill.fabric_comments) > 50 else group_bill.fabric_comments
        pdf.cell(content_width - 25, 2, comment_text, 0)
    
    # SINGLE COLUMN LAYOUT DESIGN
    table_start_y = 37 if group_bill.fabric_comments else 35
    
    # Column headers - optimized for single column
    headers = ["Date", "Image", "Fabric/Serial", "Color", "Type", "Yards", "Unit Price", "Value"]
    
    # Column widths for compact single column layout
    col_widths = [15, 16, 35, 15, 12, 15, 20, 25]
    
    # Header background
    pdf.set_fill_color(*dark_gray)
    pdf.rect(margin, table_start_y, content_width, 4, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    
    # Header text
    x_pos = margin
    for i, header in enumerate(headers):
        pdf.set_xy(x_pos, table_start_y + 1)
        pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
        x_pos += col_widths[i]
    
    # Group lines by fabric tax invoice number
    fabric_tax_groups = {}
    for line in lines:
        fabric_tax_inv = line.get('fabric_tax_invoice_number', None)
        if fabric_tax_inv not in fabric_tax_groups:
            fabric_tax_groups[fabric_tax_inv] = []
        fabric_tax_groups[fabric_tax_inv].append(line)
    
    # Table content with proper pagination
    current_y = table_start_y + 4
    fabric_tax_group_totals = {}
    max_y = 280  # Maximum Y position before new page (A4 height ~297mm, leave margin)
    page_row_count = 0  # Track rows on current page
    
    for fabric_tax_inv, group_lines in fabric_tax_groups.items():
        # Process each line in this fabric tax group - no header above data
        fabric_tax_group_total = 0
        group_line_idx = 0  # Reset line index for each group
        
        for group_line in group_lines:
            # Calculate row position based on current page row count
            row_y = current_y + (page_row_count * 18)
            
            # Check if we need a new page
            if row_y + 18 > max_y:
                pdf.add_page()
                
                # Add minimal header on continuation page
                pdf.set_fill_color(*white)
                pdf.rect(0, 0, page_width, 12, 'F')
                pdf.set_text_color(*black)
                pdf.set_font("Arial", 'B', 12)
                pdf.set_xy(0, 2)
                pdf.cell(page_width, 4, "M.S.K TEXTILE TRADING", ln=0, align='C')
                pdf.set_font("Arial", '', 6)
                pdf.set_xy(0, 7)
                pdf.cell(page_width, 3, "Professional Garment Manufacturing & Trading", ln=0, align='C')
                
                # Document title
                pdf.set_fill_color(*black)
                pdf.rect(margin, 15, content_width, 6, 'F')
                pdf.set_text_color(*white)
                pdf.set_font("Arial", 'B', 7)
                pdf.set_xy(margin, 17)
                pdf.cell(content_width, 3, "FABRIC USED (CONTINUED)", ln=0, align='C')
                
                # Table headers
                continuation_table_start_y = 25
                pdf.set_fill_color(*dark_gray)
                pdf.rect(margin, continuation_table_start_y, content_width, 4, 'F')
                pdf.set_text_color(*white)
                pdf.set_font("Arial", 'B', 7)
                x_pos = margin
                for i, header in enumerate(headers):
                    pdf.set_xy(x_pos, continuation_table_start_y + 1)
                    pdf.cell(col_widths[i], 2, header, 0, 0, 'C')
                    x_pos += col_widths[i]
                
                # Reset for new page
                current_y = continuation_table_start_y + 4
                page_row_count = 0  # Reset row count for new page
                row_y = current_y  # First row on new page
                
                # Reset text formatting for content rendering
                pdf.set_text_color(*black)
                pdf.set_font("Arial", '', 7)
            
            # Row background
            if group_line_idx % 2 == 0:
                pdf.set_fill_color(*white)
            else:
                pdf.set_fill_color(*light_gray)
            pdf.rect(margin, row_y, content_width, 18, 'F')
            
            # Row border
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(margin, row_y, content_width, 18, 'D')
            
            x_pos = margin
            
            # Date
            pdf.set_text_color(*black)
            pdf.set_font("Arial", '', 7)
            pdf.set_xy(x_pos + 1, row_y + 1)
            pl_date = format_ddmmyy(group_line.get('pl_created_at')) if group_line.get('pl_created_at') else ''
            pdf.cell(col_widths[0] - 2, 16, pl_date, 0, 0, 'C')
            x_pos += col_widths[0]
            
            # Image
            img_path = image_map.get(group_line.get('image_id'))
            if img_path and os.path.exists(img_path):
                try:
                    img_width = min(16, col_widths[1] - 2)
                    img_height = min(16, 16)
                    pdf.image(img_path, x_pos + 1, row_y + 1, img_width, img_height)
                except:
                    pass
            x_pos += col_widths[1]
            
            # Fabric/Serial - Two lines
            pdf.set_xy(x_pos + 1, row_y + 1)
            fabric_text = str(group_line['fabric_name'] or '')
            if len(fabric_text) > 30:
                fabric_text = fabric_text[:27] + "..."
            pdf.cell(col_widths[2] - 2, 8, fabric_text, 0, 0, 'C')
            
            pdf.set_xy(x_pos + 1, row_y + 9)
            serial_text = str(group_line['stitching_invoice_number'] or '')
            pdf.cell(col_widths[2] - 2, 8, serial_text, 0, 0, 'C')
            x_pos += col_widths[2]
            
            # Color
            pdf.set_xy(x_pos + 1, row_y + 1)
            color_text = str(group_line['color'] or '')
            if len(color_text) > 12:
                color_text = color_text[:9] + "..."
            pdf.cell(col_widths[3] - 2, 16, color_text, 0, 0, 'C')
            x_pos += col_widths[3]
            
            # Type (Primary/Secondary)
            pdf.set_xy(x_pos + 1, row_y + 1)
            type_text = "Primary" if group_line.get('is_primary', True) else "Secondary"
            pdf.cell(col_widths[4] - 2, 16, type_text, 0, 0, 'C')
            x_pos += col_widths[4]
            
            # Yards consumed
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.cell(col_widths[5] - 2, 16, f"{group_line['yards_consumed']:.2f}", 0, 0, 'C')
            x_pos += col_widths[5]
            
            # Unit price
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.cell(col_widths[6] - 2, 16, f"{group_line['unit_price']:,.2f}", 0, 0, 'C')
            x_pos += col_widths[6]
            
            # Value
            pdf.set_xy(x_pos + 1, row_y + 1)
            pdf.cell(col_widths[7] - 2, 16, f"{group_line['total_value']:,.2f}", 0, 0, 'C')
            
            # Add to fabric tax group total
            fabric_tax_group_total += float(group_line['total_value'] or 0)
            group_line_idx += 1
            page_row_count += 1  # Increment page row counter
        
        # Fabric tax group subtotal (minimal) - shows fabric tax invoice number here
        fabric_tax_group_totals[fabric_tax_inv] = fabric_tax_group_total
        pdf.set_font("Arial", 'B', 7)
        pdf.set_text_color(*black)
        fabric_tax_total_y = current_y + (page_row_count * 18) + 1
        pdf.set_xy(margin + 5, fabric_tax_total_y)
        pdf.cell(content_width - 10, 3, f"Total for Fabric Tax Invoice {fabric_tax_inv if fabric_tax_inv else '(None)'}: {fabric_tax_group_total:,.2f} THB", ln=0)
        
        # Move current_y to after this group for next group
        current_y = fabric_tax_total_y + 6  # After group total + 6mm gap between groups
        page_row_count += 1  # Account for the group total row
    
    # Calculate totals
    total_fabric_used = sum(line['yards_consumed'] for line in lines)
    total_fabric_value = sum(line['total_value'] for line in lines)
    
    # Summary section (minimal) - positioned after all groups with small gap
    summary_start_y = current_y + 3  # Small gap after last group total
    
    # Summary box (minimal) - reduced height like fabric invoice
    summary_height = 15  # Reduced from 20 to 15
    pdf.set_draw_color(*black)
    pdf.rect(margin, summary_start_y, content_width, summary_height, 'D')
    
    # Summary content
    pdf.set_font("Arial", 'B', 7)
    pdf.set_text_color(*black)
    pdf.set_xy(margin + 5, summary_start_y + 3)
    pdf.cell(40, 3, "FABRIC SUMMARY", ln=0)
    
    pdf.set_font("Arial", '', 7)
    pdf.set_xy(margin + 5, summary_start_y + 8)
    pdf.cell(40, 3, "Total Yards:", ln=0)
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(60, 3, f"{total_fabric_used:.2f} yards", ln=1)
    
    # Calculate final total (fabric price already includes VAT)
    fabric_grand_total = total_fabric_value
    
    # Final total (minimal) - light grey background with black border
    final_start_y = summary_start_y + summary_height + 5  # Use summary_height instead of fixed 25
    
    pdf.set_fill_color(*light_gray)
    pdf.rect(margin, final_start_y, content_width, 8, 'F')
    pdf.set_draw_color(*black)
    pdf.rect(margin, final_start_y, content_width, 8, 'D')
    pdf.set_text_color(*black)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_xy(margin + 5, final_start_y + 2)
    pdf.cell(content_width - 10, 4, f"TOTAL FABRIC PAYMENT DUE: {fabric_grand_total:,.2f} THB", ln=0, align='C')
    
    # Minimal footer
    footer_y = final_start_y + 12
    pdf.set_fill_color(*black)
    pdf.rect(0, footer_y, page_width, 6, 'F')
    pdf.set_text_color(*white)
    pdf.set_font("Arial", 'B', 7)
    pdf.set_xy(0, footer_y + 2)
    pdf.cell(page_width, 3, "FABRIC USED INVOICE COMPLETED", ln=0, align='C')
    
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
                    'beta_tax_invoice_number': stitching_invoice.invoice_line.invoice.tax_invoice_number if stitching_invoice.invoice_line and stitching_invoice.invoice_line.invoice else None,
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
                    'tax_invoice_number': packing_list.tax_invoice_number if packing_list else None,
                    'garment_fabrics': [fabric.to_dict() for fabric in stitching_invoice.garment_fabrics],
                    'lining_fabrics': [lining.to_dict() for lining in stitching_invoice.lining_fabrics]
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
            
            # FIXED: Add secondary fabric values
            secondary_fabric_value = 0
            for garment_fabric in rec.get('garment_fabrics', []):
                secondary_fabric_value += float(garment_fabric.get('total_fabric_cost', 0))
            
            record_fabric_value = fabric_value + secondary_fabric_value
            print(f"DEBUG: Main fabric value: {fabric_value}, Secondary fabric value: {secondary_fabric_value}, Total: {record_fabric_value}")
            print(f"DEBUG: garment_fabrics count: {len(rec.get('garment_fabrics', []))}")
            stitching_value = rec.get('total_value') or 0
            
            total_fabric_used += yards_consumed
            total_fabric_value += record_fabric_value
            total_stitching_value += stitching_value
            
            packing_lists[pl_serial]['fabric_used'] += yards_consumed
            packing_lists[pl_serial]['fabric_value'] += record_fabric_value
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


@group_bills_bp.route('/commission-sales', methods=['GET'])
def get_commission_sales():
    """Get all commission sales for the group bills page"""
    try:
        from app.models.commission_sale import CommissionSale
        
        # Get query parameters for filtering
        customer = request.args.get('customer')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = CommissionSale.query
        
        if customer:
            query = query.filter(CommissionSale.customer_name.ilike(f'%{customer}%'))
        
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
        
        # Convert to dictionary format
        result = []
        for sale in commission_sales:
            sale_dict = {
                'id': sale.id,
                'serial_number': sale.serial_number,
                'commission_date': sale.sale_date.isoformat() if sale.sale_date else None,
                'invoice_number': sale.invoice_line.invoice.invoice_number if sale.invoice_line and sale.invoice_line.invoice else None,
                'customer_name': sale.customer_name,
                'item_name': sale.item_name,
                'color': sale.color,
                'commission_yards': float(sale.yards_sold) if sale.yards_sold else 0,
                'unit_price': float(sale.unit_price) if sale.unit_price else 0,
                'commission_amount': float(sale.commission_amount) if sale.commission_amount else 0,
                'total_sale_value': float(sale.yards_sold * sale.unit_price) if sale.yards_sold and sale.unit_price else 0,
                'delivery_note': sale.invoice_line.delivery_note if sale.invoice_line else None,
                'delivered_location': sale.delivered_location
            }
            result.append(sale_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500