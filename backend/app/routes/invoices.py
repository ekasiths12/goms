from flask import Blueprint

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/', methods=['GET'])
def get_invoices():
    """Get all invoices - TODO: Implement"""
    return {'message': 'Invoices endpoint - TODO: Implement'}, 200
