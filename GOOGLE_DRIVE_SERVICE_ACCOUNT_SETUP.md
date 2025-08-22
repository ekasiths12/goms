# Google Drive Service Account Setup for Railway

This guide will help you set up Google Drive integration using a Service Account, which is the recommended approach for Railway deployment.

## Why Service Account?

- ✅ **One-time setup** - done forever
- ✅ **No user interaction required**
- ✅ **More reliable for server environments**
- ✅ **Recommended for production apps**
- ✅ **No OAuth2 flow issues**

## Step 1: Create Service Account in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if needed)
3. Go to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **Service Account**
5. Fill in the details:
   - **Service account name**: `goms-railway-service`
   - **Service account ID**: `goms-railway-service`
   - **Description**: `Service account for GOMS Railway app`
6. Click **CREATE AND CONTINUE**
7. For **Role**, select **Editor** (or **Owner** if you want full access)
8. Click **DONE**

## Step 2: Enable Google Drive API

1. Go to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click on **Google Drive API**
4. Click **ENABLE**

## Step 3: Create Service Account Key

1. Go back to **APIs & Services** → **Credentials**
2. Click on your service account (`goms-railway-service`)
3. Go to **KEYS** tab
4. Click **ADD KEY** → **Create new key**
5. Choose **JSON** format
6. Click **CREATE**
7. The JSON file will download automatically

## Step 4: Set Up Railway Environment Variable

1. Open the downloaded JSON file
2. Copy the **entire JSON content** (it should look like this):
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "goms-railway-service@your-project-id.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/goms-railway-service%40your-project-id.iam.gserviceaccount.com"
}
```

3. Go to your Railway project dashboard
4. Go to **Variables** tab
5. Add a new variable:
   - **Name**: `GOOGLE_CREDENTIALS`
   - **Value**: Paste the entire JSON content
6. Click **Save**

## Step 5: Share Google Drive Folder (Optional)

If you want to restrict access to a specific folder:

1. Create a folder in your Google Drive
2. Right-click the folder → **Share**
3. Add your service account email: `goms-railway-service@your-project-id.iam.gserviceaccount.com`
4. Give it **Editor** access
5. Click **Send**

## Step 6: Deploy and Test

1. Commit and push your changes
2. Railway will automatically redeploy
3. Check the logs to see if authentication is working
4. Test the Google Drive integration

## Troubleshooting

### "No GOOGLE_CREDENTIALS environment variable found"
- Make sure you added the `GOOGLE_CREDENTIALS` variable in Railway
- Check that the JSON content is complete and valid

### "Failed to parse GOOGLE_CREDENTIALS JSON"
- Make sure you copied the entire JSON content
- Check for any extra characters or formatting issues

### "Service account does not have access"
- Make sure you enabled the Google Drive API
- Check that the service account has the correct permissions
- If using a specific folder, make sure you shared it with the service account

## Security Notes

- Keep your service account key secure
- Never commit the JSON file to version control
- The key is automatically encrypted in Railway
- You can revoke and regenerate keys if needed

## Benefits of Service Account

1. **No User Interaction**: Works automatically without user login
2. **Reliable**: No OAuth2 flow issues or token expiration problems
3. **Secure**: Uses service account credentials instead of user tokens
4. **Production Ready**: Recommended for server applications
5. **One-time Setup**: Configure once and it works forever

This approach is much more reliable than OAuth2 for Railway deployment and eliminates the authentication issues you were experiencing.
