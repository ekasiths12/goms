from flask import Blueprint, request, jsonify, current_app
from app.models.stitching import StitchingInvoice, GarmentFabric, LiningFabric
from app.models.invoice import InvoiceLine, Invoice
from app.models.customer import Customer
from app.models.packing_list import PackingList, PackingListLine
from app.models.image import Image
from app.models.serial_counter import SerialCounter
from app.models.stitched_item import StitchedItem
from app.models.stitching_cost import StitchingCost
from app.models.stitching_price import StitchingPrice
from datetime import datetime
import json
import os
import shutil

# Import db from extensions
from extensions import db

stitching_bp = Blueprint('stitching', __name__)

@stitching_bp.route('/', methods=['GET'])
def get_stitching():
    """Get all stitching records with optional filters"""
    try:
        
        # Get query parameters for filtering
        pl_number = request.args.get('pl_number')
        serial_number = request.args.get('serial_number')
        fabric_name = request.args.get('fabric_name')
        customer = request.args.get('customer')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        delivered_only = request.args.get('delivered_only', 'false').lower() == 'true'
        undelivered_only = request.args.get('undelivered_only', 'false').lower() == 'true'
        
        # Build query with image relationship loaded
        query = StitchingInvoice.query.options(db.joinedload(StitchingInvoice.image))
        
        if pl_number:
            query = query.join(PackingListLine).join(PackingList).filter(
                PackingList.packing_list_serial.ilike(f'%{pl_number}%')
            )
        
        if serial_number:
            query = query.filter(StitchingInvoice.stitching_invoice_number.ilike(f'%{serial_number}%'))
        
        if fabric_name:
            query = query.filter(StitchingInvoice.item_name.ilike(f'%{fabric_name}%'))
        
        if customer:
            query = query.join(InvoiceLine).join(Invoice).join(Customer).filter(
                Customer.short_name.ilike(f'%{customer}%')
            )
        
        if date_from:
            query = query.filter(StitchingInvoice.created_at >= date_from)
        
        if date_to:
            query = query.filter(StitchingInvoice.created_at <= date_to)
        
        # Apply delivery status filter
        if delivered_only:
            # Show only records that have a packing list number (delivered)
            query = query.join(PackingListLine).filter(PackingListLine.stitching_invoice_id.isnot(None))
        elif undelivered_only:
            # Show only records that don't have a packing list number (undelivered)
            query = query.filter(~StitchingInvoice.id.in_(
                db.session.query(PackingListLine.stitching_invoice_id).filter(PackingListLine.stitching_invoice_id.isnot(None))
            ))
        
        # Order by creation date (newest first)
        query = query.order_by(StitchingInvoice.created_at.desc())
        
        # Execute query
        stitching_records = query.all()
        
        # Convert to dictionary format with additional data for treeview
        result = []
        for record in stitching_records:
            # Debug: Check image relationship
            print(f"🔍 Debug: Stitching record {record.id} - image_id: {record.image_id}, has image: {hasattr(record, 'image')}, image object: {record.image}")
            
            record_dict = record.to_dict()
            
            # Get packing list information
            packing_list_number = None
            if record.packing_list_lines:
                packing_list_number = record.packing_list_lines[0].packing_list.packing_list_serial if record.packing_list_lines[0].packing_list else None
            
            # Get fabric invoice information
            fabric_invoice_number = None
            tax_invoice_number = None
            customer_name = None
            color = None
            delivery_note = None
            fabric_unit_price = None
            
            if record.invoice_line:
                fabric_invoice_number = record.invoice_line.invoice.invoice_number if record.invoice_line.invoice else None
                tax_invoice_number = record.invoice_line.invoice.tax_invoice_number if record.invoice_line.invoice else None
                customer_name = record.invoice_line.invoice.customer.short_name if record.invoice_line.invoice and record.invoice_line.invoice.customer else None
                color = record.invoice_line.color
                delivery_note = record.invoice_line.delivery_note
                fabric_unit_price = record.invoice_line.unit_price
            
            # Add additional fields for treeview
            record_dict.update({
                'packing_list_number': packing_list_number,
                'fabric_invoice_number': fabric_invoice_number,
                'tax_invoice_number': tax_invoice_number,
                'customer_name': customer_name,
                'color': color,
                'delivery_note': delivery_note,
                'fabric_unit_price': fabric_unit_price,
                'garment_fabrics': [fabric.to_dict() for fabric in record.garment_fabrics],
                'lining_fabrics': [lining.to_dict() for lining in record.lining_fabrics]
            })
            
            # Add invoice line details for amendment
            if record.invoice_line:
                record_dict['invoice_line'] = {
                    'id': record.invoice_line.id,
                    'yards_sent': record.invoice_line.yards_sent,
                    'yards_consumed': record.invoice_line.yards_consumed,
                    'pending_yards': record.invoice_line.yards_sent - (record.invoice_line.yards_consumed or 0)
                }
            
            result.append(record_dict)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/generate-serial', methods=['POST'])
def generate_stitching_serial():
    """Generate a new stitching record serial number"""
    try:
        serial_number = SerialCounter.generate_serial_number("ST")
        return jsonify({
            'success': True,
            'serial_number': serial_number
        })
    except Exception as e:
        return jsonify({'error': f'Failed to generate serial number: {str(e)}'}), 500

@stitching_bp.route('/create', methods=['POST'])
def create_stitching_record():
    """Create a new stitching record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['selected_lines', 'stitched_item', 'size_qty', 'price', 'add_vat']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Generate serial number
        serial_number = SerialCounter.generate_serial_number("ST")
        
        # Get selected invoice lines
        selected_lines = data['selected_lines']
        if not selected_lines:
            return jsonify({'error': 'No invoice lines selected'}), 400
        
        # Calculate total yardage consumed
        total_yard_consumed = sum(line.get('consumed', 0) for line in selected_lines)
        
        # Calculate total value
        size_qty = data['size_qty']
        total_qty = sum(size_qty.values())
        price = float(data['price'])
        base_total = price * total_qty
        
        if data['add_vat']:
            total_value = base_total * 1.07  # Add 7% VAT
        else:
            total_value = base_total
        
        # Handle image data if provided
        image_id = None
        if data.get('image_data'):
            # Image was already uploaded via the images endpoint
            image_data = data['image_data']
            image_id = image_data.get('image_id')
            
            # Update the image record with stitching-specific information if needed
            if image_id:
                image = Image.query.get(image_id)
                if image:
                    # The image is already saved with AWS S3
                    # No additional processing needed
                    pass
        
        # Create stitching record
        stitching_record = StitchingInvoice(
            stitching_invoice_number=serial_number,
            item_name=selected_lines[0]['item_name'],
            yard_consumed=total_yard_consumed,
            stitched_item=data['stitched_item'],
            size_qty_json=json.dumps(size_qty),
            price=price,
            total_value=total_value,
            add_vat=data['add_vat'],
            stitching_cost=float(data.get('stitching_cost', 0)),  # Add stitching cost field
            created_at=datetime.utcnow(),
            invoice_line_id=selected_lines[0]['id'],
            image_id=image_id
        )
        
        db.session.add(stitching_record)
        db.session.flush()  # Get the ID
        
        # Add lining fabrics if provided
        lining_total_cost = 0
        if data.get('lining_fabrics'):
            for lining_data in data['lining_fabrics']:
                lining = LiningFabric(
                    stitching_invoice_id=stitching_record.id,
                    lining_name=lining_data['name'],
                    consumption_yards=lining_data['consumption'],
                    unit_price=lining_data['unit_price'],
                    total_cost=lining_data['consumption'] * lining_data['unit_price'],
                    created_at=datetime.utcnow()
                )
                db.session.add(lining)
                lining_total_cost += lining.total_cost
        
        # Add garment fabrics if provided
        fabric_total_cost = 0
        if data.get('garment_fabrics'):
            for fabric_data in data['garment_fabrics']:
                garment_fabric = GarmentFabric(
                    stitching_invoice_id=stitching_record.id,
                    fabric_invoice_line_id=fabric_data['invoice_line_id'],
                    consumption_yards=fabric_data['consumption'],
                    unit_price=fabric_data['unit_price'],
                    total_fabric_cost=fabric_data['consumption'] * fabric_data['unit_price'],
                    created_at=datetime.utcnow()
                )
                db.session.add(garment_fabric)
                fabric_total_cost += garment_fabric.total_fabric_cost
                
                # Update the invoice line's yards_consumed
                invoice_line = InvoiceLine.query.get(fabric_data['invoice_line_id'])
                if invoice_line:
                    invoice_line.yards_consumed = (invoice_line.yards_consumed or 0) + fabric_data['consumption']
        
        # Update total costs
        if lining_total_cost > 0:
            stitching_record.total_lining_cost = lining_total_cost
        if fabric_total_cost > 0:
            stitching_record.total_fabric_cost = fabric_total_cost
        
        # Update fabric invoice lines (for the main selected lines)
        for line_data in selected_lines:
            invoice_line = InvoiceLine.query.get(line_data['id'])
            if invoice_line:
                consumed = line_data.get('consumed', 0)
                invoice_line.yards_consumed = (invoice_line.yards_consumed or 0) + consumed
        
        # Memorize the cost and price if provided
        # Get the invoice line to access delivery location and customer info
        invoice_line = InvoiceLine.query.get(selected_lines[0]['id'])
        print(f"🔍 Debug: Invoice line found: {invoice_line is not None}")
        print(f"🔍 Debug: Stitching cost provided: {data.get('stitching_cost')}")
        print(f"🔍 Debug: Price provided: {data.get('price')}")
        
        if invoice_line and data.get('stitching_cost'):
            # Get delivery location from the invoice line
            delivered_location = invoice_line.delivered_location
            print(f"🔍 Debug: Delivery location: {delivered_location}")
            if delivered_location:
                print(f"💰 Memorizing cost: {data['stitched_item']} at {delivered_location} = {data['stitching_cost']}")
                StitchingCost.create_or_update_cost(
                    garment_name=data['stitched_item'],
                    stitching_location=delivered_location,
                    cost=float(data['stitching_cost'])
                )
                print(f"✅ Cost memorized successfully")
            else:
                print(f"⚠️ No delivery location found for cost memorization")
        
        if invoice_line and data.get('price'):
            # Get customer ID from the invoice line's invoice
            if invoice_line.invoice and invoice_line.invoice.customer_id:
                print(f"💵 Memorizing price: {data['stitched_item']} for customer {invoice_line.invoice.customer_id} = {data['price']}")
                StitchingPrice.create_or_update_price(
                    garment_name=data['stitched_item'],
                    customer_id=invoice_line.invoice.customer_id,
                    price=float(data['price'])
                )
                print(f"✅ Price memorized successfully")
            else:
                print(f"⚠️ No customer found for price memorization")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Stitching record {serial_number} created successfully',
            'stitching_record': stitching_record.to_dict()
        })
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/<int:stitching_id>', methods=['GET'])
def get_stitching_record(stitching_id):
    """Get a specific stitching record by ID"""
    try:
        stitching_record = StitchingInvoice.query.get_or_404(stitching_id)
        result = stitching_record.to_dict()
        
        # Add related data
        result['garment_fabrics'] = [fabric.to_dict() for fabric in stitching_record.garment_fabrics]
        result['lining_fabrics'] = [lining.to_dict() for lining in stitching_record.lining_fabrics]
        
        # Add invoice line details for amendment
        if stitching_record.invoice_line:
            result['invoice_line'] = {
                'id': stitching_record.invoice_line.id,
                'yards_sent': stitching_record.invoice_line.yards_sent,
                'yards_consumed': stitching_record.invoice_line.yards_consumed,
                'pending_yards': stitching_record.invoice_line.yards_sent - (stitching_record.invoice_line.yards_consumed or 0)
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/<int:stitching_id>/amend', methods=['PUT'])
def amend_stitching_record(stitching_id):
    """Amend a stitching record"""
    try:
        data = request.get_json()
        
        # Get the stitching record
        stitching_record = StitchingInvoice.query.get_or_404(stitching_id)
        
        # Check if it's already billed
        if stitching_record.billing_group_id:
            return jsonify({'error': 'Cannot amend billed stitching record'}), 400
        
        # Update basic fields
        stitching_record.stitched_item = data.get('stitched_item', stitching_record.stitched_item)
        stitching_record.price = float(data.get('price', stitching_record.price))
        stitching_record.stitching_cost = float(data.get('stitching_cost', stitching_record.stitching_cost or 0))
        stitching_record.add_vat = data.get('add_vat', stitching_record.add_vat)
        stitching_record.size_qty_json = json.dumps(data.get('size_qty', {}))
        
        # Calculate new total value
        size_qty = data.get('size_qty', {})
        total_qty = sum(size_qty.values())
        price = float(data.get('price', 0))
        base_total = price * total_qty
        
        if data.get('add_vat'):
            total_value = base_total * 1.07  # Add 7% VAT
        else:
            total_value = base_total
        
        stitching_record.total_value = total_value
        
        # Update fabric consumption
        fabric_consumption = data.get('fabric_consumption', {})
        if 'main' in fabric_consumption and stitching_record.invoice_line_id:
            # Calculate the difference in consumption
            old_consumption = float(stitching_record.yard_consumed or 0)
            new_consumption = float(fabric_consumption['main'])
            consumption_diff = new_consumption - old_consumption
            
            # Update the invoice line consumption
            invoice_line = InvoiceLine.query.get(stitching_record.invoice_line_id)
            if invoice_line:
                current_consumed = float(invoice_line.yards_consumed or 0)
                invoice_line.yards_consumed = current_consumed + consumption_diff
            
            # Update stitching record consumption
            stitching_record.yard_consumed = new_consumption
        
        # Update multi-fabric consumption
        multi_fabric_consumption = data.get('multi_fabric_consumption', [])
        for fabric_data in multi_fabric_consumption:
            fabric = GarmentFabric.query.get(fabric_data['id'])
            if fabric:
                # Calculate the difference in consumption
                old_consumption = float(fabric.consumption_yards or 0)
                new_consumption = float(fabric_data['consumption_yards'])
                consumption_diff = new_consumption - old_consumption
                
                # Update the fabric invoice line consumption
                if fabric.fabric_invoice_line_id:
                    fabric_invoice_line = InvoiceLine.query.get(fabric.fabric_invoice_line_id)
                    if fabric_invoice_line:
                        current_consumed = float(fabric_invoice_line.yards_consumed or 0)
                        fabric_invoice_line.yards_consumed = current_consumed + consumption_diff
                
                # Update fabric consumption and cost
                fabric.consumption_yards = new_consumption
                fabric.total_fabric_cost = new_consumption * float(fabric.unit_price or 0)
        
        # Update lining consumption
        lining_consumption = data.get('lining_consumption', [])
        for lining_data in lining_consumption:
            lining = LiningFabric.query.get(lining_data['id'])
            if lining:
                new_consumption = float(lining_data['consumption_yards'])
                lining.consumption_yards = new_consumption
                lining.total_cost = new_consumption * float(lining.unit_price or 0)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': f'Stitching record {stitching_record.stitching_invoice_number} amended successfully',
            'stitching_record': stitching_record.to_dict()
        })
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/<int:stitching_id>', methods=['DELETE'])
def delete_stitching_record(stitching_id):
    """Delete a stitching record and revert fabric inventory changes"""
    try:
        stitching_record = StitchingInvoice.query.get_or_404(stitching_id)
        
        # Check if it's already billed
        if stitching_record.billing_group_id:
            return jsonify({'error': 'Cannot delete billed stitching record'}), 400
        
        # Check if stitching record is included in any packing lists
        from app.models.packing_list import PackingListLine
        packing_list_lines = PackingListLine.query.filter_by(stitching_invoice_id=stitching_record.id).all()
        if packing_list_lines:
            packing_list_names = [pl.packing_list.packing_list_serial for pl in packing_list_lines if pl.packing_list]
            return jsonify({
                'error': f'Cannot delete - included in packing list(s): {", ".join(packing_list_names)}'
            }), 400
        
        try:
            # 1. Revert fabric inventory changes (main fabric)
            if stitching_record.yard_consumed and stitching_record.invoice_line:
                fabric_name = stitching_record.invoice_line.item_name
                if fabric_name:
                    # Update fabric inventory
                    from app.models.invoice import FabricInventory
                    fabric_inventory = FabricInventory.query.filter_by(item_name=fabric_name).first()
                    
                    if fabric_inventory:
                        fabric_inventory.total_consumed = float(fabric_inventory.total_consumed or 0) - float(stitching_record.yard_consumed)
                        fabric_inventory.pending_amount = float(fabric_inventory.pending_amount or 0) + float(stitching_record.yard_consumed)
                    else:
                        # Create inventory entry if it doesn't exist
                        fabric_inventory = FabricInventory(
                            item_name=fabric_name,
                            total_delivered=0,
                            total_consumed=0,
                            total_defective=0,
                            pending_amount=float(stitching_record.yard_consumed)
                        )
                        db.session.add(fabric_inventory)
            
            # 2. Remove from packing_list_lines
            from app.models.packing_list import PackingListLine
            PackingListLine.query.filter_by(stitching_invoice_id=stitching_record.id).delete()
            
            # 3. Remove from stitching_invoice_group_lines
            from app.models.group_bill import StitchingInvoiceGroupLine
            StitchingInvoiceGroupLine.query.filter_by(stitching_invoice_id=stitching_record.id).delete()
            
            # 4. Set billing_group_id to NULL
            stitching_record.billing_group_id = None
            
            # 5. Delete associated image file and database entry
            if stitching_record.image_id:
                from app.models.image import Image
                image_record = Image.query.get(stitching_record.image_id)
                if image_record and image_record.file_path:
                    try:
                        import os
                        if os.path.exists(image_record.file_path):
                            os.remove(image_record.file_path)
                    except Exception as e:
                        # Log warning but continue with deletion
                        print(f"Warning: Could not delete image file {image_record.file_path}: {e}")
                
                # Set image_id to NULL in stitching record first
                stitching_record.image_id = None
                
                # Delete image database entry
                if image_record:
                    db.session.delete(image_record)
            
            # 6. Revert secondary fabric consumption from garment_fabrics BEFORE deleting them
            for garment_fabric in stitching_record.garment_fabrics:
                if garment_fabric.fabric_invoice_line_id and garment_fabric.consumption_yards:
                    fabric_invoice_line = InvoiceLine.query.get(garment_fabric.fabric_invoice_line_id)
                    if fabric_invoice_line:
                        current_consumed = float(fabric_invoice_line.yards_consumed or 0)
                        fabric_invoice_line.yards_consumed = current_consumed - float(garment_fabric.consumption_yards)
            
            # 7. Revert fabric consumed in invoice line
            if stitching_record.yard_consumed and stitching_record.invoice_line_id:
                invoice_line = InvoiceLine.query.get(stitching_record.invoice_line_id)
                if invoice_line:
                    current_consumed = float(invoice_line.yards_consumed or 0)
                    invoice_line.yards_consumed = current_consumed - float(stitching_record.yard_consumed)
            
            # 8. Delete child records (garment_fabrics and lining_fabrics) before parent
            for garment_fabric in stitching_record.garment_fabrics:
                db.session.delete(garment_fabric)
            
            for lining_fabric in stitching_record.lining_fabrics:
                db.session.delete(lining_fabric)
            
            # 9. Delete stitching record
            db.session.delete(stitching_record)
            
            # Commit transaction
            db.session.commit()
            
            return jsonify({
                'message': f'Stitching record {stitching_record.stitching_invoice_number} deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/bulk-delete', methods=['DELETE'])
def bulk_delete_stitching_records():
    """Delete multiple stitching records and revert fabric inventory changes"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({'error': 'No record IDs provided'}), 400
        
        deleted_count = 0
        errors = []
        
        for record_id in record_ids:
            try:
                stitching_record = StitchingInvoice.query.get(record_id)
                if not stitching_record:
                    errors.append(f"Record ID {record_id}: Not found in database")
                    continue
                
                # Check if it's already billed
                if stitching_record.billing_group_id:
                    errors.append(f"Record {stitching_record.stitching_invoice_number}: Cannot delete billed stitching record")
                    continue
                
                # Check if stitching record is included in any packing lists
                packing_list_lines = PackingListLine.query.filter_by(stitching_invoice_id=stitching_record.id).all()
                if packing_list_lines:
                    packing_list_names = [pl.packing_list.packing_list_serial for pl in packing_list_lines if pl.packing_list]
                    errors.append(f"Record {stitching_record.stitching_invoice_number}: Cannot delete - included in packing list(s): {', '.join(packing_list_names)}")
                    continue
                
                try:
                    # 1. Revert fabric inventory changes (main fabric)
                    if stitching_record.yard_consumed and stitching_record.invoice_line:
                        fabric_name = stitching_record.invoice_line.item_name
                        if fabric_name:
                            # Update fabric inventory
                            from app.models.invoice import FabricInventory
                            fabric_inventory = FabricInventory.query.filter_by(item_name=fabric_name).first()
                            
                            if fabric_inventory:
                                fabric_inventory.total_consumed = float(fabric_inventory.total_consumed or 0) - float(stitching_record.yard_consumed)
                                fabric_inventory.pending_amount = float(fabric_inventory.pending_amount or 0) + float(stitching_record.yard_consumed)
                            else:
                                # Create inventory entry if it doesn't exist
                                fabric_inventory = FabricInventory(
                                    item_name=fabric_name,
                                    total_delivered=0,
                                    total_consumed=0,
                                    total_defective=0,
                                    pending_amount=float(stitching_record.yard_consumed)
                                )
                                db.session.add(fabric_inventory)
                    
                    # 2. Remove from packing_list_lines
                    PackingListLine.query.filter_by(stitching_invoice_id=stitching_record.id).delete()
                    
                    # 3. Remove from stitching_invoice_group_lines
                    from app.models.group_bill import StitchingInvoiceGroupLine
                    StitchingInvoiceGroupLine.query.filter_by(stitching_invoice_id=stitching_record.id).delete()
                    
                    # 4. Set billing_group_id to NULL
                    stitching_record.billing_group_id = None
                    
                    # 5. Delete associated image file and database entry
                    if stitching_record.image_id:
                        image_record = Image.query.get(stitching_record.image_id)
                        if image_record and image_record.file_path:
                            try:
                                if os.path.exists(image_record.file_path):
                                    os.remove(image_record.file_path)
                            except Exception as e:
                                # Log warning but continue with deletion
                                print(f"Warning: Could not delete image file {image_record.file_path}: {e}")
                        
                        # Set image_id to NULL in stitching record first
                        stitching_record.image_id = None
                        
                        # Delete image database entry
                        if image_record:
                            db.session.delete(image_record)
                    
                    # 6. Revert secondary fabric consumption from garment_fabrics BEFORE deleting them
                    for garment_fabric in stitching_record.garment_fabrics:
                        if garment_fabric.fabric_invoice_line_id and garment_fabric.consumption_yards:
                            fabric_invoice_line = InvoiceLine.query.get(garment_fabric.fabric_invoice_line_id)
                            if fabric_invoice_line:
                                current_consumed = float(fabric_invoice_line.yards_consumed or 0)
                                fabric_invoice_line.yards_consumed = current_consumed - float(garment_fabric.consumption_yards)
                    
                    # 7. Revert fabric consumed in invoice line
                    if stitching_record.yard_consumed and stitching_record.invoice_line_id:
                        invoice_line = InvoiceLine.query.get(stitching_record.invoice_line_id)
                        if invoice_line:
                            current_consumed = float(invoice_line.yards_consumed or 0)
                            invoice_line.yards_consumed = current_consumed - float(stitching_record.yard_consumed)
                    
                    # 8. Delete child records (garment_fabrics and lining_fabrics) before parent
                    for garment_fabric in stitching_record.garment_fabrics:
                        db.session.delete(garment_fabric)
                    
                    for lining_fabric in stitching_record.lining_fabrics:
                        db.session.delete(lining_fabric)
                    
                    # 9. Delete stitching record
                    db.session.delete(stitching_record)
                    
                    # Commit transaction for this record
                    db.session.commit()
                    deleted_count += 1
                    
                except Exception as e:
                    # Rollback transaction for this record
                    db.session.rollback()
                    error_msg = f"Record {stitching_record.stitching_invoice_number}: {str(e)}"
                    errors.append(error_msg)
                    continue
                
            except Exception as e:
                error_msg = f"Record ID {record_id}: {str(e)}"
                errors.append(error_msg)
                continue
        
        # Prepare response
        if deleted_count > 0:
            success_msg = f"Successfully deleted {deleted_count} stitching record(s)."
            if errors:
                success_msg += f"\n\nErrors:\n" + "\n".join(errors)
            return jsonify({'message': success_msg, 'deleted_count': deleted_count, 'errors': errors})
        else:
            error_msg = "No records were deleted.\n\nErrors:\n" + "\n".join(errors)
            return jsonify({'error': error_msg, 'errors': errors}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stitching_bp.route('/available-fabrics', methods=['GET'])
def get_available_fabrics():
    """Get available fabrics for multi-fabric selection"""
    try:
        
        # Get fabrics with pending yardage
        query = """
            SELECT 
                l.id,
                l.item_name,
                l.color,
                l.unit_price,
                l.delivery_note,
                l.delivered_location,
                i.invoice_number,
                c.short_name as customer_name,
                (l.yards_sent - COALESCE(l.yards_consumed, 0)) as pending_yards
            FROM invoice_lines l
            JOIN invoices i ON l.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE (l.yards_sent - COALESCE(l.yards_consumed, 0)) > 0
            ORDER BY l.item_name, l.color
        """
        
        result = db.session.execute(db.text(query))
        fabrics = []
        
        for row in result:
            fabrics.append({
                'id': row.id,
                'item_name': row.item_name,
                'color': row.color,
                'unit_price': float(row.unit_price) if row.unit_price else 0,
                'invoice_number': row.invoice_number,
                'customer_name': row.customer_name,
                'delivery_note': row.delivery_note,
                'delivered_location': row.delivered_location,
                'pending_yards': float(row.pending_yards) if row.pending_yards else 0
            })
        
        return jsonify(fabrics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== STITCHED ITEMS MANAGEMENT ENDPOINTS =====

@stitching_bp.route('/stitched-items', methods=['GET'])
def get_stitched_items():
    """Get all stitched items"""
    try:
        items = StitchedItem.get_all_items()
        return jsonify([item.to_dict() for item in items]), 200
    except Exception as e:
        return {'error': str(e)}, 500

@stitching_bp.route('/stitched-items', methods=['POST'])
def create_stitched_item():
    """Create a new stitched item"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return {'error': 'Item name is required'}, 400
        
        # Check if item already exists
        existing = StitchedItem.get_by_name(name)
        if existing:
            return {'error': f'Item "{name}" already exists'}, 400
        
        item = StitchedItem.create_item(name)
        db.session.commit()
        
        return {'message': f'Item "{name}" created successfully', 'item': item.to_dict()}, 201
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

@stitching_bp.route('/stitched-items/<int:item_id>', methods=['DELETE'])
def delete_stitched_item(item_id):
    """Delete a stitched item"""
    try:
        success = StitchedItem.delete_item(item_id)
        if not success:
            return {'error': 'Item not found'}, 404
        
        db.session.commit()
        return {'message': 'Item deleted successfully'}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': str(e)}, 500

# ===== AUTO-POPULATION ENDPOINTS =====

@stitching_bp.route('/auto-populate-cost', methods=['GET'])
def get_auto_populate_cost():
    """Get memorized cost for auto-population in stitching record creation"""
    try:
        garment_name = request.args.get('garment_name')
        stitching_location = request.args.get('stitching_location')
        
        print(f"🔍 Auto-populate cost request: garment='{garment_name}', location='{stitching_location}'")
        
        if not garment_name or not stitching_location:
            return jsonify({'error': 'Garment name and stitching location are required'}), 400
        
        cost_entry = StitchingCost.get_by_garment_and_location(garment_name, stitching_location)
        print(f"🔍 Cost entry found: {cost_entry is not None}")
        
        if cost_entry:
            print(f"💰 Returning memorized cost: {cost_entry.cost}")
            return jsonify({'cost': float(cost_entry.cost)}), 200
        else:
            print(f"ℹ️ No memorized cost found")
            return jsonify({'cost': None}), 200
        
    except Exception as e:
        print(f"❌ Error in auto-populate cost: {str(e)}")
        return jsonify({'error': f'Error fetching memorized cost: {str(e)}'}), 500

@stitching_bp.route('/auto-populate-price', methods=['GET'])
def get_auto_populate_price():
    """Get memorized price for auto-population in stitching record creation"""
    try:
        garment_name = request.args.get('garment_name')
        customer_id = request.args.get('customer_id')
        
        print(f"🔍 Auto-populate price request: garment='{garment_name}', customer_id='{customer_id}'")
        
        if not garment_name or not customer_id:
            return jsonify({'error': 'Garment name and customer ID are required'}), 400
        
        price_entry = StitchingPrice.get_by_garment_and_customer(garment_name, customer_id)
        print(f"🔍 Price entry found: {price_entry is not None}")
        
        if price_entry:
            print(f"💵 Returning memorized price: {price_entry.price}")
            return jsonify({'price': float(price_entry.price)}), 200
        else:
            print(f"ℹ️ No memorized price found")
            return jsonify({'price': None}), 200
        
    except Exception as e:
        print(f"❌ Error in auto-populate price: {str(e)}")
        return jsonify({'error': f'Error fetching memorized price: {str(e)}'}), 500
