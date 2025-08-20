from flask import Blueprint, render_template, send_from_directory, redirect, url_for
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/test')
def test():
    """Test route to check if routing is working"""
    return {'message': 'Main blueprint is working', 'status': 'ok'}

@main_bp.route('/')
def index():
    """Redirect to dashboard"""
    return redirect('/dashboard')

@main_bp.route('/dashboard')
def dashboard():
    """Serve the dashboard page"""
    return send_from_directory('../frontend', 'dashboard.html')

@main_bp.route('/fabric-invoices')
def fabric_invoices():
    """Serve the fabric invoices page"""
    return send_from_directory('../frontend', 'fabric-invoices.html')

@main_bp.route('/stitching-records')
def stitching_records():
    """Serve the stitching records page"""
    return send_from_directory('../frontend', 'stitching-records.html')

@main_bp.route('/packing-lists')
def packing_lists():
    """Serve the packing lists page"""
    return send_from_directory('../frontend', 'packing-lists.html')

@main_bp.route('/group-bills')
def group_bills():
    """Serve the group bills page"""
    return send_from_directory('../frontend', 'group-bills.html')

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory('static', 'favicon.ico')
