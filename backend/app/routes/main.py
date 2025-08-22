from flask import Blueprint, render_template, send_from_directory, redirect, url_for, jsonify
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/test')
def test():
    """Test route to check if routing is working"""
    return {'message': 'Main blueprint is working', 'status': 'ok'}

@main_bp.route('/')
def index():
    """Redirect to fabric invoices"""
    return redirect('/fabric-invoices')

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

@main_bp.route('/test-google-drive', methods=['GET'])
def test_google_drive():
    """Test Google Drive connection"""
    try:
        from app.services.google_drive_service import GoogleDriveService
        
        drive_service = GoogleDriveService()
        
        if not drive_service.is_available():
            return jsonify({
                'status': 'error',
                'message': 'Google Drive service is not available',
                'details': 'Check your GOOGLE_CREDENTIALS environment variable'
            }), 500
        
        # Try to list files to test the connection
        try:
            results = drive_service.service.files().list(pageSize=1).execute()
            return jsonify({
                'status': 'success',
                'message': 'Google Drive connection successful',
                'details': f'Found {len(results.get("files", []))} files in Drive'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': 'Google Drive connection failed',
                'details': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize Google Drive service',
            'details': str(e)
        }), 500

@main_bp.route('/debug-google-drive', methods=['GET'])
def debug_google_drive():
    """Debug Google Drive credentials"""
    try:
        credentials_json = os.getenv('GOOGLE_CREDENTIALS')
        
        if not credentials_json:
            return jsonify({
                'status': 'error',
                'message': 'GOOGLE_CREDENTIALS environment variable is not set',
                'details': 'Please add the Service Account JSON to Railway environment variables'
            }), 500
        
        try:
            import json
            creds_data = json.loads(credentials_json)
            
            return jsonify({
                'status': 'success',
                'message': 'GOOGLE_CREDENTIALS found and parsed successfully',
                'details': {
                    'type': creds_data.get('type', 'unknown'),
                    'project_id': creds_data.get('project_id', 'unknown'),
                    'client_email': creds_data.get('client_email', 'unknown'),
                    'has_private_key': 'private_key' in creds_data,
                    'private_key_length': len(creds_data.get('private_key', '')) if 'private_key' in creds_data else 0
                }
            })
            
        except json.JSONDecodeError as e:
            return jsonify({
                'status': 'error',
                'message': 'GOOGLE_CREDENTIALS is not valid JSON',
                'details': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Error checking Google Drive credentials',
            'details': str(e)
        }), 500
