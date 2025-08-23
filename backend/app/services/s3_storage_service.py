import boto3
import os
from datetime import datetime
from PIL import Image as PILImage
import io
from botocore.exceptions import ClientError, NoCredentialsError

class S3StorageService:
    """Service for handling file storage operations using AWS S3"""
    
    def __init__(self):
        # AWS S3 configuration
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.environ.get('AWS_S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME environment variable is required")
        
        # S3 folder structure
        self.images_folder = 'images'
        self.uploads_folder = 'uploads'
        self.pdfs_folder = 'pdfs'
    
    def is_available(self):
        """Check if S3 storage service is available"""
        try:
            # Test S3 connection by listing objects (limited to 1)
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"S3 storage service not available: {e}")
            return False
    
    def upload_image(self, image_data, filename, mime_type='image/jpeg'):
        """
        Upload an image to S3
        
        Args:
            image_data: Image data (bytes or file-like object)
            filename: Name for the file
            mime_type: MIME type of the image
        
        Returns:
            dict: File metadata including S3 key and URL
        """
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Determine S3 key based on file type
            if mime_type.startswith('image/'):
                s3_key = f"{self.images_folder}/{unique_filename}"
            else:
                s3_key = f"{self.uploads_folder}/{unique_filename}"
            
            # If image_data is bytes, convert to file-like object
            if isinstance(image_data, bytes):
                image_data = io.BytesIO(image_data)
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                image_data,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': mime_type
                    # Removed ACL since bucket doesn't support it
                    # Files will be publicly accessible via bucket policy instead
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # Get file size
            try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                file_size = response['ContentLength']
            except:
                file_size = 0
            
            return {
                'file_path': s3_key,  # Store S3 key as file_path
                's3_url': s3_url,
                'filename': unique_filename,
                'size': file_size,
                'mime_type': mime_type
            }
            
        except Exception as e:
            print(f"Error uploading image to S3: {e}")
            raise
    
    def upload_image_from_path(self, file_path, filename=None):
        """
        Upload an image from a local file path to S3
        
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
    
    def get_file_path(self, s3_key):
        """
        Get S3 URL from S3 key (for backward compatibility)
        
        Args:
            s3_key: S3 key stored in database
        
        Returns:
            str: S3 URL
        """
        return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
    
    def file_exists(self, s3_key):
        """
        Check if file exists in S3
        
        Args:
            s3_key: S3 key stored in database
        
        Returns:
            bool: True if file exists
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def delete_file(self, s3_key):
        """
        Delete a file from S3
        
        Args:
            s3_key: S3 key stored in database
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception as e:
            print(f"Error deleting file from S3: {e}")
            return False
    
    def list_files(self, folder='images'):
        """
        List all files in an S3 folder
        
        Args:
            folder: Folder to list (images, uploads, or pdfs)
        
        Returns:
            list: List of file metadata
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{folder}/"
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip the folder itself
                    if obj['Key'].endswith('/'):
                        continue
                    
                    files.append({
                        'filename': os.path.basename(obj['Key']),
                        'path': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat(),
                        'url': f"https://{self.bucket_name}.s3.amazonaws.com/{obj['Key']}"
                    })
            
            return files
            
        except Exception as e:
            print(f"Error listing files from S3: {e}")
            return []
    
    def get_file_url(self, s3_key):
        """
        Generate a URL for accessing the file
        
        Args:
            s3_key: S3 key stored in database
        
        Returns:
            str: URL for accessing the file
        """
        return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
    
    def download_file(self, s3_key, local_path):
        """
        Download a file from S3 to local path
        
        Args:
            s3_key: S3 key stored in database
            local_path: Local path to save the file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except Exception as e:
            print(f"Error downloading file from S3: {e}")
            return False
