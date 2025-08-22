# Google Drive OAuth2 Setup for Railway Deployment

## Overview

This guide explains how to set up Google Drive OAuth2 integration for your Railway deployment at `goms.up.railway.app`. The local `token.pickle` file won't work on Railway due to its ephemeral file system and security considerations.

## OAuth2 Setup for Railway

### Step 1: Create OAuth2 Credentials in Google Cloud Console

1. **Go to Google Cloud Console**:
   - Visit [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Select your project (or create one if you haven't already)

2. **Navigate to Credentials**:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client IDs**

3. **Configure OAuth Consent Screen** (if not already done):
   - Choose **External** user type
   - Fill in required fields:
     - App name: `Garment Management System`
     - User support email: Your email
     - Developer contact information: Your email
   - Add scopes: `https://www.googleapis.com/auth/drive.file`
   - Add test users: Your email address

4. **Create OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Name: `GOMS Railway App`
   - **Authorized redirect URIs** (add these):
     ```
     https://goms.up.railway.app/oauth2callback
     http://localhost:8080/oauth2callback
     http://localhost:5000/oauth2callback
     ```
   - Click **Create**

5. **Download the JSON file**:
   - Click the download button (⬇️) next to your new OAuth 2.0 Client ID
   - Save the file as `oauth2_credentials.json`

### Step 2: Configure Railway Environment Variables

1. **Open Railway Dashboard**:
   - Go to your Railway project dashboard
   - Navigate to **Variables** tab

2. **Add Environment Variables**:
   - **Name**: `GOOGLE_CREDENTIALS`
   - **Value**: Copy the entire contents of the downloaded OAuth2 JSON file
   
   - **Name**: `GOOGLE_DRIVE_FOLDER_ID`
   - **Value**: Your Google Drive folder ID (e.g., `1TLnjpJuMWdllq3VOgw_kH-EyGRISq6cg`)

3. **Example Environment Variables**:
   ```bash
   GOOGLE_CREDENTIALS={"web":{"client_id":"your-client-id.apps.googleusercontent.com","project_id":"your-project-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["https://goms.up.railway.app/oauth2callback"]}}
   GOOGLE_DRIVE_FOLDER_ID=1TLnjpJuMWdllq3VOgw_kH-EyGRISq6cg
   ```

### Step 3: Deploy and Initialize OAuth2

1. **Deploy to Railway**:
   - Push your code to trigger a new deployment
   - Wait for the deployment to complete

2. **Access OAuth2 Setup Page**:
   - Visit: `https://goms.up.railway.app/oauth2-setup`
   - This page will help you complete the OAuth2 setup

3. **Initialize OAuth2 Flow**:
   - Click "Start OAuth2 Authorization" button
   - You'll be redirected to Google's authorization page
   - Sign in with your Google account
   - Grant permissions to the application
   - You'll be redirected back to your app

### Step 4: Test the Integration

1. **Check Status**:
   - Visit the OAuth2 setup page to verify Google Drive is available
   - Or check: `https://goms.up.railway.app/api/health`

2. **Test Upload**:
   - Go to any page with image upload functionality
   - Try uploading an image
   - Check if it appears in your Google Drive folder

## Troubleshooting

### Common Issues

1. **"OAuth2 flow requires user interaction"**
   - Visit `/oauth2-setup` page to start the authorization flow
   - Make sure you're signed in with the correct Google account

2. **"Invalid redirect URI"**
   - Verify the redirect URIs in Google Cloud Console match exactly:
     - `https://goms.up.railway.app/oauth2callback`
   - Check for typos or extra spaces

3. **"Google Drive features will be disabled"**
   - Check that `GOOGLE_CREDENTIALS` environment variable is set correctly
   - Verify the JSON format is valid
   - Ensure you've completed the OAuth2 authorization flow

4. **"Permission denied" errors**
   - Make sure you've granted the necessary permissions during OAuth2 flow
   - Check that the folder ID is correct

### Debug Steps

1. **Check Railway Logs**:
   - Go to Railway dashboard → Deployments → View logs
   - Look for Google Drive related errors

2. **Verify Environment Variables**:
   - Check Railway Variables tab
   - Ensure `GOOGLE_CREDENTIALS` and `GOOGLE_DRIVE_FOLDER_ID` are set

3. **Test OAuth2 Flow**:
   - Visit `/oauth2-setup` page
   - Use the "Check Status" button to verify setup

## Security Notes

- ✅ OAuth2 credentials are stored securely in Railway environment variables
- ✅ No sensitive files are committed to the repository
- ✅ Each Railway deployment uses its own isolated credentials
- ✅ Credentials can be rotated without code changes
- ✅ OAuth2 tokens are handled securely through the callback flow

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
4. Complete the OAuth2 authorization flow
5. Test the Google Drive integration

The app will automatically detect the environment and use the appropriate authentication method.

## Quick Setup Checklist

- [ ] Created OAuth2 credentials in Google Cloud Console
- [ ] Added redirect URI: `https://goms.up.railway.app/oauth2callback`
- [ ] Downloaded OAuth2 JSON file
- [ ] Set `GOOGLE_CREDENTIALS` environment variable in Railway
- [ ] Set `GOOGLE_DRIVE_FOLDER_ID` environment variable in Railway
- [ ] Deployed to Railway
- [ ] Visited `/oauth2-setup` page
- [ ] Completed OAuth2 authorization flow
- [ ] Tested image upload functionality
