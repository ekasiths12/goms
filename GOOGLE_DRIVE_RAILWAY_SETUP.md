# Google Drive Integration Setup for Railway Deployment

## Overview

This guide explains how to set up Google Drive integration for your Railway deployment. The local `token.pickle` file won't work on Railway due to its ephemeral file system and security considerations.

## Two Authentication Methods

### Method 1: Service Account (Recommended for Railway)

Service accounts are perfect for server-to-server authentication and don't require user interaction.

#### Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Click **Create Credentials** > **Service Account**
4. Fill in the details:
   - **Name**: `garment-app-service-account`
   - **Description**: `Service account for garment management app`
5. Click **Create and Continue**
6. Skip role assignment (we'll handle permissions manually)
7. Click **Done**

#### Step 2: Generate Service Account Key

1. Click on your newly created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create New Key**
4. Choose **JSON** format
5. Download the JSON file

#### Step 3: Set Up Google Drive Permissions

1. Open the downloaded JSON file
2. Copy the `client_email` value (looks like: `garment-app@project-id.iam.gserviceaccount.com`)
3. Go to your Google Drive folder
4. Right-click the folder > **Share**
5. Add the service account email with **Editor** permissions
6. Make sure to uncheck "Notify people" to avoid sending emails

#### Step 4: Configure Railway Environment Variable

1. Open your Railway project dashboard
2. Go to **Variables** tab
3. Add a new variable:
   - **Name**: `GOOGLE_CREDENTIALS`
   - **Value**: Copy the entire contents of the downloaded JSON file
4. Click **Add**

### Method 2: OAuth2 Credentials (Alternative)

If you prefer to use OAuth2, you'll need to handle the authentication flow differently.

#### Step 1: Create OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Click **Create Credentials** > **OAuth 2.0 Client IDs**
4. Choose **Web application**
5. Add authorized redirect URIs:
   - `https://your-railway-app.railway.app/oauth2callback`
   - `http://localhost:8080/oauth2callback` (for local development)
6. Download the JSON file

#### Step 2: Configure Railway Environment Variable

1. Open your Railway project dashboard
2. Go to **Variables** tab
3. Add a new variable:
   - **Name**: `GOOGLE_CREDENTIALS`
   - **Value**: Copy the entire contents of the OAuth2 JSON file
4. Click **Add**

## Environment Variables Summary

Add these to your Railway project:

```bash
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
```

## Testing the Setup

After deployment, you can test the Google Drive integration by:

1. Uploading an image through your app
2. Checking if it appears in your Google Drive folder
3. Verifying the file permissions and access

## Troubleshooting

### Common Issues

1. **"Google Drive features will be disabled"**
   - Check that `GOOGLE_CREDENTIALS` environment variable is set correctly
   - Verify the JSON format is valid
   - Ensure the service account has access to the Google Drive folder

2. **"Permission denied" errors**
   - Make sure the service account email has Editor permissions on the Google Drive folder
   - Check that the folder ID is correct

3. **"Invalid credentials" errors**
   - Verify the JSON credentials are complete and properly formatted
   - Ensure the service account is enabled in Google Cloud Console

### Debug Mode

To enable debug logging, add this environment variable:
```bash
GOOGLE_DRIVE_DEBUG=true
```

## Security Notes

- ✅ Service account credentials are stored securely in Railway environment variables
- ✅ No sensitive files are committed to the repository
- ✅ Each Railway deployment uses its own isolated credentials
- ✅ Credentials can be rotated without code changes

## Local Development

For local development, you can still use the `token.pickle` approach:

1. Keep `credentials.json` in your local `backend/` directory
2. Run the authentication flow locally to generate `token.pickle`
3. These files are now in `.gitignore` and won't be committed

## Migration from Local to Railway

If you're migrating from local development:

1. Remove `token.pickle` and `credentials.json` from your local repository
2. Set up the Railway environment variables as described above
3. Deploy to Railway
4. Test the Google Drive integration

The app will automatically detect the environment and use the appropriate authentication method.
