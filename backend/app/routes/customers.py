from flask import Blueprint, request, jsonify
from app import db
from app.models.customer import Customer

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/', methods=['GET'])
def get_customers():
    """Get all customers"""
    try:
        customers = Customer.query.order_by(Customer.short_name).all()
        return jsonify({
            'success': True,
            'data': [customer.to_dict() for customer in customers]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
