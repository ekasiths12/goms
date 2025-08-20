from flask import Blueprint, render_template, send_from_directory
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory('static', 'favicon.ico')
