#!/usr/bin/env python3
"""
Migration script to move images from Railway volume storage to AWS S3

This script will:
1. Find all existing images in the database
2. Download them from Railway volumes (if they exist)
3. Upload them to S3
4. Update the database with new S3 keys
5. Clean up old files

Usage:
    python migrate_images_to_s3.py

Environment variables required:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - AWS_S3_BUCKET_NAME
    - DATABASE_URL
"""

import os
import sys
import tempfile
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from extensions import db
from app.models.image import Image
from app.services.s3_storage_service import S3StorageService

def migrate_images_to_s3():
    """Migrate all images from Railway volumes to S3"""
    
    print("🚀 Starting image migration from Railway volumes to AWS S3...")
    
    # Initialize Flask app and database
    app = create_app()
    
    with app.app_context():
        try:
            # Initialize S3 service
            s3_service = S3StorageService()
            
            # Check S3 connectivity
            if not s3_service.is_available():
                print("❌ S3 service is not available. Please check your AWS credentials.")
                return False
            
            print(f"✅ S3 service is available. Using bucket: {s3_service.bucket_name}")
            
            # Get all images from database
            images = Image.query.all()
            print(f"📊 Found {len(images)} images in database")
            
            if not images:
                print("ℹ️  No images found in database. Migration complete.")
                return True
            
            migrated_count = 0
            skipped_count = 0
            error_count = 0
            
            for image in images:
                try:
                    print(f"\n🔄 Processing image ID {image.id}: {image.file_path}")
                    
                    # Check if image already exists in S3
                    if s3_service.file_exists(image.file_path):
                        print(f"   ✅ Image already exists in S3: {image.file_path}")
                        skipped_count += 1
                        continue
                    
                    # Try to download from Railway volume (if it exists)
                    old_file_path = None
                    if os.path.exists(image.file_path):
                        old_file_path = image.file_path
                    elif os.path.exists(f"/app/static/{image.file_path}"):
                        old_file_path = f"/app/static/{image.file_path}"
                    elif os.path.exists(f"static/{image.file_path}"):
                        old_file_path = f"static/{image.file_path}"
                    
                    if old_file_path and os.path.exists(old_file_path):
                        print(f"   📥 Found old file at: {old_file_path}")
                        
                        # Upload to S3
                        try:
                            result = s3_service.upload_image_from_path(old_file_path, os.path.basename(image.file_path))
                            
                            # Update database with new S3 key
                            old_file_path = image.file_path
                            image.file_path = result['file_path']
                            db.session.commit()
                            
                            print(f"   ✅ Uploaded to S3: {result['file_path']}")
                            print(f"   🔗 S3 URL: {result['s3_url']}")
                            
                            # Optionally delete old file (uncomment if you want to clean up)
                            # os.remove(old_file_path)
                            # print(f"   🗑️  Deleted old file: {old_file_path}")
                            
                            migrated_count += 1
                            
                        except Exception as e:
                            print(f"   ❌ Error uploading to S3: {e}")
                            error_count += 1
                    else:
                        print(f"   ⚠️  Old file not found: {image.file_path}")
                        print(f"   💡 This image may have been lost or already migrated")
                        skipped_count += 1
                
                except Exception as e:
                    print(f"   ❌ Error processing image {image.id}: {e}")
                    error_count += 1
            
            # Print summary
            print(f"\n📋 Migration Summary:")
            print(f"   ✅ Successfully migrated: {migrated_count}")
            print(f"   ⏭️  Skipped: {skipped_count}")
            print(f"   ❌ Errors: {error_count}")
            print(f"   📊 Total processed: {len(images)}")
            
            if error_count == 0:
                print(f"\n🎉 Migration completed successfully!")
                return True
            else:
                print(f"\n⚠️  Migration completed with {error_count} errors.")
                return False
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

def verify_migration():
    """Verify that all images are accessible via S3"""
    
    print("\n🔍 Verifying migration...")
    
    app = create_app()
    
    with app.app_context():
        try:
            s3_service = S3StorageService()
            images = Image.query.all()
            
            accessible_count = 0
            inaccessible_count = 0
            
            for image in images:
                try:
                    if s3_service.file_exists(image.file_path):
                        accessible_count += 1
                        print(f"   ✅ Image {image.id} accessible: {image.file_path}")
                    else:
                        inaccessible_count += 1
                        print(f"   ❌ Image {image.id} not accessible: {image.file_path}")
                except Exception as e:
                    inaccessible_count += 1
                    print(f"   ❌ Image {image.id} error: {e}")
            
            print(f"\n📊 Verification Summary:")
            print(f"   ✅ Accessible: {accessible_count}")
            print(f"   ❌ Inaccessible: {inaccessible_count}")
            print(f"   📊 Total: {len(images)}")
            
            return inaccessible_count == 0
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

if __name__ == "__main__":
    print("🔄 Image Migration Tool")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the migration.")
        sys.exit(1)
    
    # Run migration
    success = migrate_images_to_s3()
    
    if success:
        # Verify migration
        verify_migration()
    
    print("\n🏁 Migration tool completed.")
