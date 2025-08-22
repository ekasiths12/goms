from flask import Blueprint, render_template, send_from_directory, redirect, url_for
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/test')
def test():
    """Test route to check if routing is working"""
    return {'message': 'Main blueprint is working', 'status': 'ok'}

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory('static', 'favicon.ico')
