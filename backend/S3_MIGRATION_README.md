# AWS S3 Migration Guide

This document outlines the migration from Railway volume storage to AWS S3 for image storage in the Garment Management System.

## Overview

The application has been migrated from using Railway's persistent volumes to AWS S3 for storing uploaded images. This provides better scalability, reliability, and cost-effectiveness.

## Changes Made

### 1. New S3 Storage Service
- **File**: `backend/app/services/s3_storage_service.py`
- **Purpose**: Handles all S3 operations (upload, download, delete, list)
- **Features**:
  - Automatic file organization in S3 folders (images/, uploads/, pdfs/)
  - Public read access for direct URL access
  - Proper error handling and logging
  - Backward compatibility with existing API

### 2. Updated Image Model
- **File**: `backend/app/models/image.py`
- **Changes**:
  - `file_path` now stores S3 keys instead of local paths
  - `get_image_url()` returns S3 URLs
  - `get_image_path_for_pdf()` downloads files temporarily for PDF generation

### 3. Updated API Routes
- **File**: `backend/app/routes/images.py`
- **Changes**:
  - All uploads now go to S3
  - File deletion removes from S3
  - File listing shows S3 metadata

### 4. Updated Configuration
- **File**: `backend/config/config.py`
- **Changes**:
  - Removed Railway volume configuration
  - Added AWS S3 configuration variables
  - Updated folder paths to S3 folder names

### 5. Removed Old Code
- **Deleted**: `backend/app/services/file_storage_service.py`
- **Removed**: All Railway volume storage references

## Environment Variables Required

Add these environment variables to your deployment:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-s3-bucket-name
```

## AWS S3 Setup

### 1. Create S3 Bucket
```bash
aws s3 mb s3://your-bucket-name
```

### 2. Configure Bucket for Public Read Access
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

### 3. Configure CORS (if needed)
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Migration Process

### 1. Run Migration Script
If you have existing images in Railway volumes:

```bash
cd backend
python migrate_images_to_s3.py
```

This script will:
- Find all images in the database
- Upload them to S3
- Update database records with S3 keys
- Verify migration success

### 2. Verify Migration
The migration script includes verification to ensure all images are accessible via S3.

## API Changes

### Image Upload
- **Endpoint**: `POST /api/images/upload`
- **Response**: Now includes S3 URL instead of local path
- **Storage**: Files stored in S3 with public read access

### Image Retrieval
- **Endpoint**: `GET /api/images/<id>`
- **Response**: Includes S3 URL for direct access
- **Access**: Images accessible via direct S3 URLs

### File Serving
- **Endpoint**: `GET /api/files/static/<path>`
- **Behavior**: Now redirects to S3 URL instead of serving local files

## Benefits

1. **Scalability**: S3 can handle unlimited storage and concurrent access
2. **Reliability**: 99.99% availability with automatic replication
3. **Cost-Effective**: Pay only for what you use
4. **Global Access**: CDN integration possible for faster access
5. **Backup**: Automatic versioning and lifecycle policies available

## Troubleshooting

### Common Issues

1. **S3 Access Denied**
   - Check AWS credentials
   - Verify bucket permissions
   - Ensure bucket policy allows public read

2. **Images Not Loading**
   - Verify S3 URLs are correct
   - Check CORS configuration
   - Ensure bucket is publicly accessible

3. **Upload Failures**
   - Check file size limits
   - Verify S3 bucket exists
   - Check AWS region configuration

### Debug Endpoints

- `GET /api/images/status` - Check S3 service status
- `GET /api/images/list` - List files in S3
- `GET /api/files/file-info/<path>` - Get S3 file information

## Rollback Plan

If you need to rollback to Railway volumes:

1. Restore `backend/app/services/file_storage_service.py`
2. Update imports in affected files
3. Restore Railway volume configuration
4. Update environment variables
5. Revert database changes if needed

## Support

For issues with S3 integration, check:
1. AWS S3 documentation
2. Application logs for error messages
3. S3 bucket access logs
4. Network connectivity to AWS
