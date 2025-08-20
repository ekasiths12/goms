# Railway Deployment Guide

This guide will help you deploy the Garment Management System to Railway.app.

## Prerequisites

1. **GitHub Account**: Make sure your code is pushed to GitHub
2. **Railway Account**: Sign up at [railway.app](https://railway.app)
3. **Railway CLI** (optional): Install for local testing

## Step 1: Prepare Your Repository

1. **Push to GitHub**:
   ```bash
   cd garment_web_app
   git init
   git add .
   git commit -m "Initial web application setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

## Step 2: Deploy to Railway

### Option A: Using Railway Dashboard

1. **Go to Railway Dashboard**:
   - Visit [railway.app](https://railway.app)
   - Sign in with your GitHub account

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add MySQL Database**:
   - Click "New Service"
   - Select "Database" → "MySQL"
   - Railway will automatically create a MySQL database

4. **Configure Environment Variables**:
   - Go to your web service
   - Click "Variables" tab
   - Add the following variables:
     ```
     DATABASE_URL=mysql://username:password@host:port/database
     SECRET_KEY=your-secret-key-here
     FLASK_DEBUG=False
     ```
   - Railway will automatically provide the `DATABASE_URL` from the MySQL service

5. **Deploy**:
   - Railway will automatically deploy your application
   - The deployment will run the `railway_start.py` script to initialize the database

### Option B: Using Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   cd garment_web_app
   railway init
   ```

4. **Add MySQL Service**:
   ```bash
   railway add
   # Select "Database" → "MySQL"
   ```

5. **Deploy**:
   ```bash
   railway up
   ```

## Step 3: Verify Deployment

1. **Check Deployment Status**:
   - Go to your Railway dashboard
   - Check the deployment logs for any errors
   - Look for the success message: "✅ Railway startup completed successfully!"

2. **Test the Application**:
   - Click on your web service to get the URL
   - Visit the URL in your browser
   - Test the health endpoint: `https://your-app.railway.app/api/health`

3. **Check Database**:
   - Go to your MySQL service in Railway
   - Check that tables were created successfully
   - Verify serial counters were initialized

## Step 4: Configure Custom Domain (Optional)

1. **Add Custom Domain**:
   - Go to your web service settings
   - Click "Domains"
   - Add your custom domain
   - Configure DNS records as instructed

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check that `DATABASE_URL` is set correctly
   - Verify MySQL service is running
   - Check deployment logs for connection errors

2. **Build Failed**:
   - Check that all dependencies are in `requirements.txt`
   - Verify Dockerfile is correct
   - Check for syntax errors in Python files

3. **Application Not Starting**:
   - Check the startup logs
   - Verify `railway_start.py` is running correctly
   - Check that port 8000 is exposed

### Debug Commands

```bash
# Check Railway logs
railway logs

# Check service status
railway status

# Connect to database
railway connect

# View environment variables
railway variables
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | MySQL connection string | Yes | Auto-provided by Railway |
| `SECRET_KEY` | Flask secret key | Yes | Auto-generated |
| `FLASK_DEBUG` | Debug mode | No | False |
| `UPLOAD_FOLDER` | File upload directory | No | static/uploads |
| `PDF_FOLDER` | PDF storage directory | No | static/pdfs |
| `IMAGE_FOLDER` | Image storage directory | No | static/images |

## Monitoring

1. **Railway Dashboard**:
   - Monitor application performance
   - Check resource usage
   - View deployment history

2. **Application Logs**:
   - Access logs through Railway dashboard
   - Monitor for errors and performance issues

3. **Database Monitoring**:
   - Check MySQL service metrics
   - Monitor connection pool usage

## Scaling

1. **Horizontal Scaling**:
   - Railway automatically scales based on traffic
   - Configure scaling rules in service settings

2. **Database Scaling**:
   - Upgrade MySQL plan for more resources
   - Consider read replicas for high traffic

## Backup Strategy

1. **Database Backups**:
   - Railway provides automatic MySQL backups
   - Configure backup frequency in MySQL service settings

2. **Application Backups**:
   - Your code is backed up in GitHub
   - Consider backing up uploaded files to external storage

## Security

1. **Environment Variables**:
   - Never commit sensitive data to Git
   - Use Railway's secure environment variable storage

2. **Database Security**:
   - Railway provides secure MySQL connections
   - Use strong passwords for database access

3. **Application Security**:
   - Keep dependencies updated
   - Monitor for security vulnerabilities

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **GitHub Issues**: Report bugs in your repository

---

**Note**: This deployment guide assumes you're using the standard Railway setup. Adjust configurations based on your specific requirements.
