import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pickle
from PIL import Image as PILImage

class GoogleDriveService:
    """Service for handling Google Drive operations"""
    
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    FOLDER_ID = '1dToY9n5R-uDigQg-Y5goTA7YOcEnE00t'  # Your Google Drive folder ID
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()
    
    def is_available(self):
        """Check if Google Drive service is available (credentials configured)"""
        try:
            return self.service is not None
        except:
            return False
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Check if credentials file exists
                if not os.path.exists('credentials.json'):
                    print("⚠️  Google Drive credentials.json not found. Google Drive features will be disabled.")
                    print("💡 To enable Google Drive uploads, download credentials.json from Google Cloud Console")
                    self.service = None
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def upload_image(self, image_data, filename, mime_type='image/jpeg'):
        """
        Upload an image to Google Drive
        
        Args:
            image_data: Image data (bytes or file-like object)
            filename: Name for the file in Google Drive
            mime_type: MIME type of the image
        
        Returns:
            dict: File metadata including file ID and web view link
        """
        try:
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.FOLDER_ID]
            }
            
            # If image_data is bytes, convert to file-like object
            if isinstance(image_data, bytes):
                image_data = io.BytesIO(image_data)
            
            # Create media upload
            media = MediaIoBaseUpload(
                image_data,
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink'
            ).execute()
            
            return {
                'file_id': file.get('id'),
                'name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink')
            }
            
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
            raise
    
    def upload_image_from_path(self, file_path, filename=None):
        """
        Upload an image from a local file path
        
        Args:
            file_path: Path to the local image file
            filename: Optional custom filename for Google Drive
        
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
    
    def generate_filename(self, garment_name, fabric_name, fabric_color):
        """
        Generate filename according to the specified format:
        Garmentname-fabricname-fabriccolor
        
        Args:
            garment_name: Name of the garment
            fabric_name: Name of the fabric
            fabric_color: Color of the fabric
        
        Returns:
            str: Formatted filename
        """
        # Clean and format the components
        garment_clean = self._clean_filename(garment_name)
        fabric_clean = self._clean_filename(fabric_name)
        color_clean = self._clean_filename(fabric_color)
        
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
    
    def list_files(self):
        """
        List all files in the configured folder
        
        Returns:
            list: List of file metadata
        """
        try:
            results = self.service.files().list(
                q=f"'{self.FOLDER_ID}' in parents",
                fields="files(id,name,webViewLink,createdTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def delete_file(self, file_id):
        """
        Delete a file from Google Drive
        
        Args:
            file_id: ID of the file to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
