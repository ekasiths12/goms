from flask import Blueprint, request, jsonify
from app.models.stitching_cost import StitchingCost
from app.models.stitching_price import StitchingPrice
from app.models.customer import Customer
from extensions import db
from datetime import datetime

cost_price_bp = Blueprint('cost_price', __name__)

# ===== COST LIST MANAGEMENT =====

@cost_price_bp.route('/costs', methods=['GET'])
def get_cost_list():
    """Get all memorized stitching costs with optional filtering"""
    try:
        # Get query parameters for filtering
        garment_name = request.args.get('garment_name')
        location = request.args.get('location')
        
        # Build query
        query = StitchingCost.query
        
        if garment_name:
            query = query.filter(StitchingCost.garment_name.ilike(f'%{garment_name}%'))
        
        if location:
            query = query.filter(StitchingCost.stitching_location.ilike(f'%{location}%'))
        
        # Order by garment name and location
        costs = query.order_by(StitchingCost.garment_name, StitchingCost.stitching_location).all()
        
        return jsonify([cost.to_dict() for cost in costs]), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching cost list: {str(e)}'}), 500

@cost_price_bp.route('/costs', methods=['POST'])
def create_cost():
    """Create a new stitching cost entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        garment_name = data.get('garment_name')
        stitching_location = data.get('stitching_location')
        cost = data.get('cost')
        
        if not garment_name or not stitching_location or cost is None:
            return jsonify({'error': 'Garment name, stitching location, and cost are required'}), 400
        
        # Validate cost is positive
        try:
            cost = float(cost)
            if cost < 0:
                return jsonify({'error': 'Cost must be a positive number'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Cost must be a valid number'}), 400
        
        # Create or update cost
        cost_entry = StitchingCost.create_or_update_cost(garment_name, stitching_location, cost)
        db.session.commit()
        
        return jsonify(cost_entry.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating cost entry: {str(e)}'}), 500

@cost_price_bp.route('/costs/<int:cost_id>', methods=['PUT'])
def update_cost(cost_id):
    """Update an existing stitching cost entry"""
    try:
        cost_entry = StitchingCost.query.get_or_404(cost_id)
        data = request.get_json()
        
        # Validate cost is positive
        if 'cost' in data:
            try:
                new_cost = float(data['cost'])
                if new_cost < 0:
                    return jsonify({'error': 'Cost must be a positive number'}), 400
                cost_entry.cost = new_cost
            except (ValueError, TypeError):
                return jsonify({'error': 'Cost must be a valid number'}), 400
        
        # Update other fields if provided
        if 'garment_name' in data:
            cost_entry.garment_name = data['garment_name']
        
        if 'stitching_location' in data:
            cost_entry.stitching_location = data['stitching_location']
        
        cost_entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(cost_entry.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating cost entry: {str(e)}'}), 500

@cost_price_bp.route('/costs/<int:cost_id>', methods=['DELETE'])
def delete_cost(cost_id):
    """Delete a stitching cost entry"""
    try:
        cost_entry = StitchingCost.query.get_or_404(cost_id)
        db.session.delete(cost_entry)
        db.session.commit()
        
        return jsonify({'message': 'Cost entry deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting cost entry: {str(e)}'}), 500

@cost_price_bp.route('/costs/auto-populate', methods=['GET'])
def get_memorized_cost():
    """Get memorized cost for a specific garment and location combination"""
    try:
        garment_name = request.args.get('garment_name')
        stitching_location = request.args.get('stitching_location')
        
        if not garment_name or not stitching_location:
            return jsonify({'error': 'Garment name and stitching location are required'}), 400
        
        cost_entry = StitchingCost.get_by_garment_and_location(garment_name, stitching_location)
        
        if cost_entry:
            return jsonify({'cost': float(cost_entry.cost)}), 200
        else:
            return jsonify({'cost': None}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching memorized cost: {str(e)}'}), 500

# ===== PRICE LIST MANAGEMENT =====

@cost_price_bp.route('/prices', methods=['GET'])
def get_price_list():
    """Get all memorized stitching prices with optional filtering"""
    try:
        # Get query parameters for filtering
        garment_name = request.args.get('garment_name')
        customer_name = request.args.get('customer_name')
        
        # Build query
        query = StitchingPrice.query.join(Customer)
        
        if garment_name:
            query = query.filter(StitchingPrice.garment_name.ilike(f'%{garment_name}%'))
        
        if customer_name:
            query = query.filter(Customer.short_name.ilike(f'%{customer_name}%'))
        
        # Order by garment name and customer
        prices = query.order_by(StitchingPrice.garment_name, Customer.short_name).all()
        
        return jsonify([price.to_dict() for price in prices]), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching price list: {str(e)}'}), 500

@cost_price_bp.route('/prices', methods=['POST'])
def create_price():
    """Create a new stitching price entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        garment_name = data.get('garment_name')
        customer_id = data.get('customer_id')
        price = data.get('price')
        
        if not garment_name or not customer_id or price is None:
            return jsonify({'error': 'Garment name, customer ID, and price are required'}), 400
        
        # Validate customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Validate price is positive
        try:
            price = float(price)
            if price < 0:
                return jsonify({'error': 'Price must be a positive number'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Price must be a valid number'}), 400
        
        # Create or update price
        price_entry = StitchingPrice.create_or_update_price(garment_name, customer_id, price)
        db.session.commit()
        
        return jsonify(price_entry.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating price entry: {str(e)}'}), 500

@cost_price_bp.route('/prices/<int:price_id>', methods=['PUT'])
def update_price(price_id):
    """Update an existing stitching price entry"""
    try:
        price_entry = StitchingPrice.query.get_or_404(price_id)
        data = request.get_json()
        
        # Validate price is positive
        if 'price' in data:
            try:
                new_price = float(data['price'])
                if new_price < 0:
                    return jsonify({'error': 'Price must be a positive number'}), 400
                price_entry.price = new_price
            except (ValueError, TypeError):
                return jsonify({'error': 'Price must be a valid number'}), 400
        
        # Update other fields if provided
        if 'garment_name' in data:
            price_entry.garment_name = data['garment_name']
        
        if 'customer_id' in data:
            # Validate customer exists
            customer = Customer.query.get(data['customer_id'])
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            price_entry.customer_id = data['customer_id']
        
        price_entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(price_entry.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating price entry: {str(e)}'}), 500

@cost_price_bp.route('/prices/<int:price_id>', methods=['DELETE'])
def delete_price(price_id):
    """Delete a stitching price entry"""
    try:
        price_entry = StitchingPrice.query.get_or_404(price_id)
        db.session.delete(price_entry)
        db.session.commit()
        
        return jsonify({'message': 'Price entry deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting price entry: {str(e)}'}), 500

@cost_price_bp.route('/prices/auto-populate', methods=['GET'])
def get_memorized_price():
    """Get memorized price for a specific garment and customer combination"""
    try:
        garment_name = request.args.get('garment_name')
        customer_id = request.args.get('customer_id')
        
        if not garment_name or not customer_id:
            return jsonify({'error': 'Garment name and customer ID are required'}), 400
        
        price_entry = StitchingPrice.get_by_garment_and_customer(garment_name, customer_id)
        
        if price_entry:
            return jsonify({'price': float(price_entry.price)}), 200
        else:
            return jsonify({'price': None}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching memorized price: {str(e)}'}), 500

# ===== UTILITY ENDPOINTS =====

@cost_price_bp.route('/costs/garments', methods=['GET'])
def get_unique_garments_for_costs():
    """Get unique garment names from cost list"""
    try:
        garments = db.session.query(StitchingCost.garment_name).distinct().order_by(StitchingCost.garment_name).all()
        return jsonify([garment[0] for garment in garments]), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching garments: {str(e)}'}), 500

@cost_price_bp.route('/costs/locations', methods=['GET'])
def get_unique_locations_for_costs():
    """Get unique stitching locations from cost list"""
    try:
        locations = db.session.query(StitchingCost.stitching_location).distinct().order_by(StitchingCost.stitching_location).all()
        return jsonify([location[0] for location in locations]), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching locations: {str(e)}'}), 500

@cost_price_bp.route('/prices/garments', methods=['GET'])
def get_unique_garments_for_prices():
    """Get unique garment names from price list"""
    try:
        garments = db.session.query(StitchingPrice.garment_name).distinct().order_by(StitchingPrice.garment_name).all()
        return jsonify([garment[0] for garment in garments]), 200
    except Exception as e:
        return jsonify({'error': f'Error fetching garments: {str(e)}'}), 500
