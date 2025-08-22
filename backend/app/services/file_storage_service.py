import os
import shutil
from datetime import datetime
from PIL import Image as PILImage
import io

class FileStorageService:
    """Service for handling file storage operations using Railway mounted volumes"""
    
    def __init__(self):
        # Use Railway's persistent volume path or fallback to local static folder
        self.base_storage_path = os.environ.get('RAILWAY_VOLUME_PATH') or '/app/static'
        self.images_path = os.path.join(self.base_storage_path, 'images')
        self.uploads_path = os.path.join(self.base_storage_path, 'uploads')
        self.pdfs_path = os.path.join(self.base_storage_path, 'pdfs')
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [self.images_path, self.uploads_path, self.pdfs_path]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def is_available(self):
        """Check if file storage service is available"""
        try:
            # Check if we can write to the storage directory
            test_file = os.path.join(self.images_path, '.test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception as e:
            print(f"File storage service not available: {e}")
            return False
    
    def upload_image(self, image_data, filename, mime_type='image/jpeg'):
        """
        Upload an image to the file storage
        
        Args:
            image_data: Image data (bytes or file-like object)
            filename: Name for the file
            mime_type: MIME type of the image
        
        Returns:
            dict: File metadata including file path and URL
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Determine storage path based on file type
            if mime_type.startswith('image/'):
                storage_path = self.images_path
            else:
                storage_path = self.uploads_path
            
            file_path = os.path.join(storage_path, unique_filename)
            
            # If image_data is bytes, convert to file-like object
            if isinstance(image_data, bytes):
                image_data = io.BytesIO(image_data)
            
            # Save the file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(image_data, f)
            
            # Generate relative path for database storage
            relative_path = os.path.relpath(file_path, self.base_storage_path)
            
            return {
                'file_path': relative_path,
                'absolute_path': file_path,
                'filename': unique_filename,
                'size': os.path.getsize(file_path),
                'mime_type': mime_type
            }
            
        except Exception as e:
            print(f"Error uploading image: {e}")
            raise
    
    def upload_image_from_path(self, file_path, filename=None):
        """
        Upload an image from a local file path
        
        Args:
            file_path: Path to the local image file
            filename: Optional custom filename
        
        Returns:
            dict: File metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        if filename is None:
            filename = os.path.basename(file_path)
        
        # Determine MIME type based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        return self.upload_image(image_data, filename, mime_type)
    
    def generate_filename(self, garment_name, fabric_name, fabric_color, stitching_serial_number=None):
        """
        Generate filename according to the specified format:
        Garmentname-fabricname-fabriccolor-stitching_serial
        
        Args:
            garment_name: Name of the garment
            fabric_name: Name of the fabric
            fabric_color: Color of the fabric
            stitching_serial_number: Stitching record serial number (optional)
        
        Returns:
            str: Formatted filename
        """
        # Clean and format the components
        garment_clean = self._clean_filename(garment_name)
        fabric_clean = self._clean_filename(fabric_name)
        color_clean = self._clean_filename(fabric_color)
        
        # Build filename
        if stitching_serial_number:
            serial_clean = self._clean_filename(stitching_serial_number)
            return f"{garment_clean}-{fabric_clean}-{color_clean}-{serial_clean}.jpg"
        else:
            return f"{garment_clean}-{fabric_clean}-{color_clean}.jpg"
    
    def _clean_filename(self, text):
        """
        Clean text for use in filename
        
        Args:
            text: Text to clean
        
        Returns:
            str: Cleaned text
        """
        if not text:
            return "unknown"
        
        # Remove special characters and replace spaces with hyphens
        import re
        cleaned = re.sub(r'[^\w\s-]', '', text)
        cleaned = re.sub(r'[-\s]+', '-', cleaned)
        cleaned = cleaned.strip('-').lower()
        
        return cleaned if cleaned else "unknown"
    
    def get_file_path(self, relative_path):
        """
        Get absolute file path from relative path
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            str: Absolute file path
        """
        return os.path.join(self.base_storage_path, relative_path)
    
    def file_exists(self, relative_path):
        """
        Check if file exists
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            bool: True if file exists
        """
        absolute_path = self.get_file_path(relative_path)
        return os.path.exists(absolute_path)
    
    def delete_file(self, relative_path):
        """
        Delete a file from storage
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            absolute_path = self.get_file_path(relative_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, directory='images'):
        """
        List all files in a directory
        
        Args:
            directory: Directory to list (images, uploads, or pdfs)
        
        Returns:
            list: List of file metadata
        """
        try:
            dir_path = os.path.join(self.base_storage_path, directory)
            if not os.path.exists(dir_path):
                return []
            
            files = []
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'filename': filename,
                        'path': os.path.join(directory, filename),
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def get_file_url(self, relative_path):
        """
        Generate a URL for accessing the file
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            str: URL for accessing the file
        """
        # For Railway, we'll serve files through Flask static routes
        return f"/static/{relative_path}"
