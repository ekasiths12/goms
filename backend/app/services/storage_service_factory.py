import os
from .s3_storage_service import S3StorageService
from .local_storage_service import LocalStorageService

class StorageServiceFactory:
    """Factory for creating storage services based on availability"""
    
    @staticmethod
    def get_storage_service():
        """
        Get the best available storage service
        
        Returns:
            StorageService: S3StorageService if available, otherwise LocalStorageService
        """
        # Check if S3 environment variables are set
        s3_configured = all([
            os.environ.get('AWS_ACCESS_KEY_ID'),
            os.environ.get('AWS_SECRET_ACCESS_KEY'),
            os.environ.get('AWS_S3_BUCKET_NAME')
        ])
        
        if s3_configured:
            try:
                # Try to create S3 service
                s3_service = S3StorageService()
                if s3_service.is_available():
                    print("✅ Using S3 storage service")
                    return s3_service
                else:
                    print("⚠️  S3 configured but not available, falling back to local storage")
            except Exception as e:
                print(f"⚠️  S3 service creation failed: {e}, falling back to local storage")
        
        # Fall back to local storage
        try:
            local_service = LocalStorageService()
            if local_service.is_available():
                print("✅ Using local storage service")
                return local_service
            else:
                raise Exception("Local storage service is not available")
        except Exception as e:
            print(f"❌ Local storage service creation failed: {e}")
            raise Exception("No storage service is available")
    
    @staticmethod
    def get_storage_service_info():
        """
        Get information about available storage services
        
        Returns:
            dict: Information about storage services
        """
        info = {
            's3_configured': False,
            's3_available': False,
            'local_available': False,
            'selected_service': None
        }
        
        # Check S3 configuration
        s3_configured = all([
            os.environ.get('AWS_ACCESS_KEY_ID'),
            os.environ.get('AWS_SECRET_ACCESS_KEY'),
            os.environ.get('AWS_S3_BUCKET_NAME')
        ])
        info['s3_configured'] = s3_configured
        
        if s3_configured:
            try:
                s3_service = S3StorageService()
                info['s3_available'] = s3_service.is_available()
            except:
                info['s3_available'] = False
        
        # Check local storage
        try:
            local_service = LocalStorageService()
            info['local_available'] = local_service.is_available()
        except:
            info['local_available'] = False
        
        # Determine selected service
        if info['s3_available']:
            info['selected_service'] = 'S3'
        elif info['local_available']:
            info['selected_service'] = 'Local'
        else:
            info['selected_service'] = 'None'
        
        return info
