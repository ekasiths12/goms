import os
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from app.models.image import Image
from app.services.file_storage_service import FileStorageService

# Create Blueprint
images_bp = Blueprint('images', __name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@images_bp.route('/upload', methods=['POST'])
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
        stitching_serial_number = request.form.get('stitching_serial_number', None)
        
        # Initialize file storage service
        try:
            storage_service = FileStorageService()
        except Exception as e:
            print(f"⚠️  File storage service error: {str(e)}")
            return jsonify({'error': f'File storage service not available: {str(e)}'}), 500
        
        # Generate filename using the storage service
        storage_filename = storage_service.generate_filename(garment_name, fabric_name, fabric_color, stitching_serial_number)
        
        # Upload to file storage
        try:
            # Read file data
            file_data = file.read()
            
            # Upload to storage service
            storage_result = storage_service.upload_image(file_data, storage_filename, file.content_type)
            
            # Save to database
            image = Image(
                file_path=storage_result['file_path'],
                uploaded_at=datetime.utcnow()
            )
            
            db.session.add(image)
            db.session.commit()
            
            # Return response
            response_data = {
                'success': True,
                'message': 'Image uploaded successfully to Railway volume storage',
                'image_id': image.id,
                'file_path': storage_result['file_path'],
                'filename': storage_result['filename'],
                'size': storage_result['size'],
                'file_url': storage_service.get_file_url(storage_result['file_path'])
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@images_bp.route('/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get image information"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        return jsonify(image.to_dict())
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving image: {str(e)}'}), 500

@images_bp.route('/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image from both local storage and Google Drive"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete from file storage
        try:
            storage_service = FileStorageService()
            storage_service.delete_file(image.file_path)
        except Exception as e:
            print(f"Error deleting from file storage: {e}")
        
        # Also try to delete local file if it exists (for backward compatibility)
        absolute_path = storage_service.get_file_path(image.file_path) if 'storage_service' in locals() else image.file_path
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Error deleting image: {str(e)}'}), 500

@images_bp.route('/list', methods=['GET'])
def list_files():
    """List all files in storage"""
    try:
        directory = request.args.get('directory', 'images')
        storage_service = FileStorageService()
        files = storage_service.list_files(directory)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'error': f'Error listing files: {str(e)}'}), 500

@images_bp.route('/status', methods=['GET'])
def storage_status():
    """Get storage service status"""
    try:
        storage_service = FileStorageService()
        status = {
            'available': storage_service.is_available(),
            'base_path': storage_service.base_storage_path,
            'images_path': storage_service.images_path,
            'uploads_path': storage_service.uploads_path,
            'pdfs_path': storage_service.pdfs_path
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting storage status: {str(e)}'}), 500
