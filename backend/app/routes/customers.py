from flask import Blueprint, request, jsonify
from app.models.customer import Customer
from app.models.customer_id_mapping import CustomerIdMapping
from main import db
import json
import os
from datetime import datetime

customers_bp = Blueprint('customers', __name__)

# Customer ID file path (similar to old Qt app)
CUSTOMER_ID_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'customer_ids.json')

# Fallback for Railway deployment
if not os.path.exists(CUSTOMER_ID_FILE):
    CUSTOMER_ID_FILE = os.path.join(os.getcwd(), 'customer_ids.json')

@customers_bp.route('/', methods=['GET'])
def get_customers():
    """Get all customers"""
    try:
        customers = Customer.query.all()
        result = []
        for customer in customers:
            result.append({
                'id': customer.id,
                'customer_id': customer.customer_id,
                'short_name': customer.short_name,
                'full_name': customer.full_name,
                'registration_date': customer.registration_date.isoformat() if customer.registration_date else None,
                'is_active': customer.is_active
            })
        return jsonify(result)
    except Exception as e:
        return {'error': str(e)}, 500

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer by ID"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        return jsonify({
            'success': True,
            'data': customer.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('customer_id') or not data.get('short_name'):
            return jsonify({
                'success': False,
                'error': 'customer_id and short_name are required'
            }), 400
        
        # Check if customer already exists
        existing_customer = Customer.get_by_customer_id(data['customer_id'])
        if existing_customer:
            return jsonify({
                'success': False,
                'error': 'Customer with this ID already exists'
            }), 400
        
        # Create new customer
        customer = Customer(
            customer_id=data['customer_id'],
            short_name=data['short_name'],
            full_name=data.get('full_name'),
            registration_date=data.get('registration_date'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()
        
        # Update fields
        if 'short_name' in data:
            customer.short_name = data['short_name']
        if 'full_name' in data:
            customer.full_name = data['full_name']
        if 'registration_date' in data:
            customer.registration_date = data['registration_date']
        if 'is_active' in data:
            customer.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': customer.to_dict(),
            'message': 'Customer updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Check if customer has related records
        if customer.invoices or customer.packing_lists or customer.group_bills:
            return jsonify({
                'success': False,
                'error': 'Cannot delete customer with existing invoices, packing lists, or group bills'
            }), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Customer deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/active', methods=['GET'])
def get_active_customers():
    """Get all active customers"""
    try:
        customers = Customer.get_active_customers()
        return jsonify({
            'success': True,
            'data': [customer.to_dict() for customer in customers]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/customer-ids', methods=['GET'])
def get_customer_ids():
    """Get selected customer IDs for .dat import filtering"""
    try:
        print("🔍 Loading customer IDs from database...")
        mappings = CustomerIdMapping.get_all_mappings()
        customer_ids = [mapping.customer_id for mapping in mappings]
        print(f"✅ Loaded {len(customer_ids)} customer IDs from database")
        return jsonify(customer_ids)
    except Exception as e:
        print(f"❌ Error loading customer IDs: {e}")
        return {'error': str(e)}, 500

@customers_bp.route('/customer-ids', methods=['POST'])
def save_customer_ids():
    """Save selected customer IDs for .dat import filtering"""
    try:
        data = request.get_json()
        customer_ids = data.get('customer_ids', [])
        
        print(f"💾 Saving {len(customer_ids)} customer IDs to database")
        
        # Clear existing mappings
        CustomerIdMapping.query.delete()
        
        # Add new mappings
        for customer_id in customer_ids:
            mapping = CustomerIdMapping(customer_id=customer_id)
            db.session.add(mapping)
        
        db.session.commit()
        print(f"✅ Successfully saved {len(customer_ids)} customer IDs to database")
        
        return jsonify({'success': True, 'message': f'Saved {len(customer_ids)} customer IDs'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving customer IDs: {e}")
        return {'error': str(e)}, 500

@customers_bp.route('/customer-id-mappings', methods=['GET'])
def get_customer_id_mappings():
    """Get customer ID mappings with short names"""
    try:
        mappings = CustomerIdMapping.get_all_mappings()
        result = [mapping.to_dict() for mapping in mappings]
        return jsonify(result)
    except Exception as e:
        return {'error': str(e)}, 500
