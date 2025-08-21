import os
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from app.models.image import Image
from app.services.google_drive_service import GoogleDriveService

# Create Blueprint
images_bp = Blueprint('images', __name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@images_bp.route('/api/images/upload', methods=['POST'])
def upload_image():
    """Upload image to both local storage and Google Drive"""
    try:
        # Check if file was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get form data for filename generation
        garment_name = request.form.get('garment_name', 'unknown')
        fabric_name = request.form.get('fabric_name', 'unknown')
        fabric_color = request.form.get('fabric_color', 'unknown')
        
        # Initialize Google Drive service
        try:
            drive_service = GoogleDriveService()
        except Exception as e:
            print(f"⚠️  Google Drive service error: {str(e)}")
            drive_service = None
        
        # Save file locally first
        filename = secure_filename(file.filename)
        upload_dir = 'static/uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        local_path = os.path.join(upload_dir, filename)
        file.save(local_path)
        
        # Generate Google Drive filename
        drive_filename = drive_service.generate_filename(garment_name, fabric_name, fabric_color) if drive_service else None
        
        # Upload to Google Drive
        try:
            if drive_service and drive_service.is_available():
                drive_result = drive_service.upload_image_from_path(local_path, drive_filename)
            
            # Save to database
            if drive_service and drive_service.is_available() and drive_result:
                image = Image(
                    file_path=local_path,
                    uploaded_at=datetime.utcnow(),
                    google_drive_id=drive_result['file_id'],
                    google_drive_link=drive_result['web_view_link'],
                    google_drive_filename=drive_result['name']
                )
                
                db.session.add(image)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Image uploaded successfully to local storage and Google Drive',
                    'image_id': image.id,
                    'local_path': local_path,
                    'google_drive_id': drive_result['file_id'],
                    'google_drive_link': drive_result['web_view_link'],
                    'google_drive_filename': drive_result['name']
                })
            else:
                # Google Drive not available, save locally only
                image = Image(
                    file_path=local_path,
                    uploaded_at=datetime.utcnow()
                )
                
                db.session.add(image)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Image uploaded to local storage (Google Drive not configured)',
                    'image_id': image.id,
                    'local_path': local_path,
                    'warning': 'Google Drive upload disabled - credentials not configured'
                })
            
        except Exception as e:
            # If Google Drive upload fails, still save locally
            image = Image(
                file_path=local_path,
                uploaded_at=datetime.utcnow()
            )
            db.session.add(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded to local storage (Google Drive upload failed)',
                'image_id': image.id,
                'local_path': local_path,
                'warning': f'Google Drive upload failed: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@images_bp.route('/api/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get image information"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify(image.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving image: {str(e)}'}), 500

@images_bp.route('/api/images/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image from both local storage and Google Drive"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete from Google Drive if exists
        if image.google_drive_id:
            try:
                drive_service = GoogleDriveService()
                drive_service.delete_file(image.google_drive_id)
            except Exception as e:
                print(f"Error deleting from Google Drive: {e}")
        
        # Delete local file
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Error deleting image: {str(e)}'}), 500

@images_bp.route('/api/images/google-drive/list', methods=['GET'])
def list_google_drive_files():
    """List all files in Google Drive folder"""
    try:
        drive_service = GoogleDriveService()
        files = drive_service.list_files()
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500

@images_bp.route('/api/images/google-drive/upload', methods=['POST'])
def upload_to_google_drive():
    """Upload existing local image to Google Drive"""
    try:
        image_id = request.json.get('image_id')
        garment_name = request.json.get('garment_name', 'unknown')
        fabric_name = request.json.get('fabric_name', 'unknown')
        fabric_color = request.json.get('fabric_color', 'unknown')
        
        if not image_id:
            return jsonify({'error': 'Image ID required'}), 400
        
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        if not os.path.exists(image.file_path):
            return jsonify({'error': 'Local image file not found'}), 404
        
        # Initialize Google Drive service
        drive_service = GoogleDriveService()
        
        # Generate filename
        drive_filename = drive_service.generate_filename(garment_name, fabric_name, fabric_color)
        
        # Upload to Google Drive
        drive_result = drive_service.upload_image_from_path(image.file_path, drive_filename)
        
        # Update database
        image.google_drive_id = drive_result['file_id']
        image.google_drive_link = drive_result['web_view_link']
        image.google_drive_filename = drive_result['name']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded to Google Drive successfully',
            'google_drive_id': drive_result['file_id'],
            'google_drive_link': drive_result['web_view_link'],
            'google_drive_filename': drive_result['name']
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload to Google Drive failed: {str(e)}'}), 500
