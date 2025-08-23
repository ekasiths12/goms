import os
import shutil
from datetime import datetime
from PIL import Image as PILImage
import io
from pathlib import Path

class LocalStorageService:
    """Service for handling file storage operations using local file system"""
    
    def __init__(self):
        # Local storage configuration
        self.base_path = Path('static/uploads')
        self.images_folder = self.base_path / 'images'
        self.uploads_folder = self.base_path / 'uploads'
        self.pdfs_folder = self.base_path / 'pdfs'
        
        # Create directories if they don't exist
        self.images_folder.mkdir(parents=True, exist_ok=True)
        self.uploads_folder.mkdir(parents=True, exist_ok=True)
        self.pdfs_folder.mkdir(parents=True, exist_ok=True)
    
    def is_available(self):
        """Check if local storage service is available"""
        try:
            # Test by trying to create a test file
            test_file = self.images_folder / 'test.txt'
            test_file.write_text('test')
            test_file.unlink()  # Remove test file
            return True
        except Exception as e:
            print(f"Local storage service not available: {e}")
            return False
    
    def upload_image(self, image_data, filename, mime_type='image/jpeg'):
        """
        Upload an image to local storage
        
        Args:
            image_data: Image data (bytes or file-like object)
            filename: Name for the file
            mime_type: MIME type of the image
        
        Returns:
            dict: File metadata including local path and URL
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Determine storage path based on file type
            if mime_type.startswith('image/'):
                storage_path = self.images_folder / unique_filename
                relative_path = f"images/{unique_filename}"
            else:
                storage_path = self.uploads_folder / unique_filename
                relative_path = f"uploads/{unique_filename}"
            
            # If image_data is bytes, convert to file-like object
            if isinstance(image_data, bytes):
                image_data = io.BytesIO(image_data)
            
            # Save to local file system
            with open(storage_path, 'wb') as f:
                shutil.copyfileobj(image_data, f)
            
            # Generate local URL (relative to static folder)
            local_url = f"/static/{relative_path}"
            
            # Get file size
            file_size = storage_path.stat().st_size
            
            return {
                'file_path': relative_path,  # Store relative path as file_path
                'local_url': local_url,
                'filename': unique_filename,
                'size': file_size,
                'mime_type': mime_type
            }
            
        except Exception as e:
            print(f"Error uploading image to local storage: {e}")
            raise
    
    def upload_image_from_path(self, file_path, filename=None):
        """
        Upload an image from a local file path to local storage
        
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
        Get local URL from relative path (for backward compatibility)
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            str: Local URL
        """
        return f"/static/{relative_path}"
    
    def file_exists(self, relative_path):
        """
        Check if file exists in local storage
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            bool: True if file exists
        """
        full_path = self.base_path / relative_path
        return full_path.exists()
    
    def delete_file(self, relative_path):
        """
        Delete a file from local storage
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            full_path = self.base_path / relative_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file from local storage: {e}")
            return False
    
    def list_files(self, folder='images'):
        """
        List all files in a local folder
        
        Args:
            folder: Folder to list (images, uploads, or pdfs)
        
        Returns:
            list: List of file metadata
        """
        try:
            folder_path = self.base_path / folder
            
            if not folder_path.exists():
                return []
            
            files = []
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    files.append({
                        'filename': file_path.name,
                        'path': f"{folder}/{file_path.name}",
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        'url': f"/static/{folder}/{file_path.name}"
                    })
            
            return files
            
        except Exception as e:
            print(f"Error listing files from local storage: {e}")
            return []
    
    def get_file_url(self, relative_path):
        """
        Generate a URL for accessing the file
        
        Args:
            relative_path: Relative path stored in database
        
        Returns:
            str: URL for accessing the file
        """
        return f"/static/{relative_path}"
    
    def download_file(self, relative_path, local_path):
        """
        Copy a file from local storage to another local path
        
        Args:
            relative_path: Relative path stored in database
            local_path: Local path to save the file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source_path = self.base_path / relative_path
            if source_path.exists():
                shutil.copy2(source_path, local_path)
                return True
            return False
        except Exception as e:
            print(f"Error copying file from local storage: {e}")
            return False
