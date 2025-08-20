from flask import Blueprint

group_bills_bp = Blueprint('group_bills', __name__)

@group_bills_bp.route('/', methods=['GET'])
def get_group_bills():
    """Get all group bills - TODO: Implement"""
    return {'message': 'Group Bills endpoint - TODO: Implement'}, 200
