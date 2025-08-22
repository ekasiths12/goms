# Google Drive Integration for Stitching Record Images

## Overview

This update integrates Google Drive storage for images uploaded when creating stitching records in the fabric invoices page. Images are now automatically uploaded to Google Drive with proper naming and can be used in PDF generation.

## Changes Made

### 1. Frontend Changes (fabric-invoices.html)

#### Image Upload Flow
- **Before**: Images were only stored locally with filename
- **After**: Images are uploaded to Google Drive with proper naming

#### Key Changes:
- Added `stitchingImageFile` variable to store the actual file
- Updated `handleImageUpload()` to store the file object instead of just filename
- Modified `submitStitchingRecord()` to:
  - Upload image to Google Drive first using `/api/images/upload`
  - Pass image data (including Google Drive info) to stitching record creation
  - Handle upload errors gracefully

#### Image Naming Convention
Images are automatically named using the format:
```
{stitched_item}-{fabric_name}-{fabric_color}.jpg
```

Example: `t-shirt-cotton-blue.jpg`

### 2. Backend Changes

#### Stitching Record Creation (stitching.py)
- **Before**: Only handled local image paths
- **After**: Accepts image data with Google Drive information
- Updated to use pre-uploaded images from the images endpoint

#### Image Model Enhancements (image.py)
- Added `get_image_url()` method: Returns Google Drive link if available, falls back to local path
- Added `get_image_path_for_pdf()` method: Returns best available path for PDF generation
- Added proper imports for file operations

#### PDF Generation Updates (packing_lists.py)
- **Before**: Used only local file paths
- **After**: Uses Google Drive images when available, falls back to local
- Updated image mapping to use the new `get_image_path_for_pdf()` method

## How It Works

### 1. Image Upload Process
1. User selects image in stitching record dialog
2. Image is previewed locally
3. When submitting stitching record:
   - Image is uploaded to Google Drive via `/api/images/upload`
   - Google Drive returns file ID, link, and filename
   - Image data is passed to stitching record creation
   - Stitching record is created with image reference

### 2. PDF Generation Process
1. PDF generation retrieves stitching records with images
2. For each image:
   - Checks if Google Drive link is available
   - Uses Google Drive image if available
   - Falls back to local image if needed
3. Images are embedded in PDFs (packing lists, fabric invoices, stitching invoices)

### 3. File Storage
- **Local Storage**: Images are still saved locally as backup
- **Google Drive**: Images are uploaded to configured Google Drive folder
- **Database**: Stores both local path and Google Drive information

## Configuration Required

### 1. Google Drive Setup
1. Create Google Cloud project
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Download `credentials.json`

### 2. Railway Environment Variables
Add these to your Railway project:
```
GOOGLE_CREDENTIALS={"your":"credentials_json_content"}
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
```

### 3. Google Drive Folder
1. Create folder in Google Drive
2. Get folder ID from URL
3. Share folder with your Google Cloud project email
4. Set `GOOGLE_DRIVE_FOLDER_ID` environment variable

## Testing

### Manual Testing
1. Start your Flask app
2. Go to Fabric Invoices page
3. Select invoice lines and click "Create Stitching Record"
4. Upload an image
5. Submit the stitching record
6. Check Google Drive folder for uploaded image
7. Generate PDFs to verify images appear

### Automated Testing
Run the test script:
```bash
python test_google_drive_integration.py
```

## Benefits

### ✅ **Improved Storage**
- Images stored in cloud (Google Drive)
- Automatic backup and redundancy
- Accessible from anywhere

### ✅ **Better Organization**
- Automatic naming based on garment/fabric/color
- Consistent file structure
- Easy to find and manage

### ✅ **PDF Integration**
- Images automatically included in PDFs
- High-quality image display
- Professional document appearance

### ✅ **Scalability**
- No local storage limitations
- Cloud-based image management
- Easy to scale with business growth

## Troubleshooting

### Common Issues

1. **"Google Drive credentials not found"**
   - Ensure `GOOGLE_CREDENTIALS` environment variable is set
   - Check that credentials.json content is valid

2. **"Image upload failed"**
   - Verify Google Drive API is enabled
   - Check folder permissions
   - Ensure folder ID is correct

3. **"Images not appearing in PDFs"**
   - Check if images were uploaded successfully
   - Verify Google Drive links are accessible
   - Check local file paths exist

### Debug Steps
1. Check Railway logs for error messages
2. Verify environment variables are set correctly
3. Test Google Drive API access manually
4. Check image upload endpoint response

## Future Enhancements

### Potential Improvements
1. **Image Compression**: Automatically compress images before upload
2. **Multiple Formats**: Support for different image formats
3. **Image Editing**: Basic image editing capabilities
4. **Bulk Operations**: Upload multiple images at once
5. **Image Search**: Search images by garment/fabric/color

### Advanced Features
1. **Image Versioning**: Keep multiple versions of images
2. **Image Analytics**: Track image usage and performance
3. **CDN Integration**: Use CDN for faster image delivery
4. **Image Watermarking**: Add watermarks to images

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Railway logs for error details
3. Test with the provided test script
4. Verify Google Drive configuration

## Migration Notes

### From Old Qt App
- Images from old Qt app will continue to work
- New images will be uploaded to Google Drive
- PDF generation will use both old and new images
- No data migration required

### Backward Compatibility
- Local image storage still works as fallback
- Existing stitching records remain functional
- PDF generation works with both old and new images
- No breaking changes to existing functionality
