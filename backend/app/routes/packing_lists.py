from flask import Blueprint

packing_lists_bp = Blueprint('packing_lists', __name__)

@packing_lists_bp.route('/', methods=['GET'])
def get_packing_lists():
    """Get all packing lists - TODO: Implement"""
    return {'message': 'Packing Lists endpoint - TODO: Implement'}, 200
