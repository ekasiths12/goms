import os
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from app.models.image import Image
from app.services.storage_service_factory import StorageServiceFactory

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
    """Upload image to AWS S3"""
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
        
        # Initialize storage service (S3 or local)
        try:
            storage_service = StorageServiceFactory.get_storage_service()
        except Exception as e:
            print(f"⚠️  Storage service error: {str(e)}")
            return jsonify({'error': f'Storage service not available: {str(e)}'}), 500
        
        # Generate filename using the storage service
        storage_filename = storage_service.generate_filename(garment_name, fabric_name, fabric_color, stitching_serial_number)
        
        # Upload to S3
        try:
            # Read file data
            file_data = file.read()
            
            # Upload to S3 storage service
            storage_result = storage_service.upload_image(file_data, storage_filename, file.content_type)
            
            # Save to database
            image = Image(
                file_path=storage_result['file_path'],  # This is now the S3 key
                uploaded_at=datetime.utcnow()
            )
            
            db.session.add(image)
            db.session.commit()
            
            # Return response
            response_data = {
                'success': True,
                'message': 'Image uploaded successfully',
                'image_id': image.id,
                'file_path': storage_result['file_path'],
                'filename': storage_result['filename'],
                'size': storage_result['size'],
                'file_url': storage_result.get('s3_url') or storage_result.get('local_url')
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
    """Delete image from AWS S3"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete from storage service
        try:
            storage_service = StorageServiceFactory.get_storage_service()
            storage_service.delete_file(image.file_path)  # file_path is now storage key
        except Exception as e:
            print(f"Error deleting from storage: {e}")
        
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
        folder = request.args.get('folder', 'images')
        storage_service = StorageServiceFactory.get_storage_service()
        files = storage_service.list_files(folder)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'error': f'Error listing files from storage: {str(e)}'}), 500

@images_bp.route('/status', methods=['GET'])
def storage_status():
    """Get storage service status"""
    try:
        storage_info = StorageServiceFactory.get_storage_service_info()
        storage_service = StorageServiceFactory.get_storage_service()
        
        status = {
            'available': storage_service.is_available(),
            'service_type': storage_info['selected_service'],
            's3_configured': storage_info['s3_configured'],
            's3_available': storage_info['s3_available'],
            'local_available': storage_info['local_available'],
            'images_folder': str(storage_service.images_folder),
            'uploads_folder': str(storage_service.uploads_folder),
            'pdfs_folder': str(storage_service.pdfs_folder)
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': f'Error getting storage status: {str(e)}'}), 500
