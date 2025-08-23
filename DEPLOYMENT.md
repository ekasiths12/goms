# 🚀 Deployment Guide

This guide covers deployment of the Garment Management System (GMS) to various platforms.

## 📋 Table of Contents

- [Railway Deployment](#railway-deployment)
- [Local Production Setup](#local-production-setup)
- [Docker Deployment](#docker-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Troubleshooting](#troubleshooting)

## 🚂 Railway Deployment

### Prerequisites
- Railway account
- GitHub repository connected to Railway
- MySQL database (Railway MySQL plugin or external)

### Step 1: Prepare Repository

1. **Ensure clean repository**
   ```bash
   # Remove development files (already done)
   git add .
   git commit -m "Clean repository for deployment"
   git push origin main
   ```

2. **Verify essential files**
   - ✅ `backend/wsgi.py` - WSGI entry point
   - ✅ `backend/Dockerfile.railway` - Docker configuration
   - ✅ `railway.json` - Railway configuration
   - ✅ `backend/requirements.txt` - Python dependencies
   - ✅ `backend/customer_ids.json` - Customer configuration

### Step 2: Railway Setup

1. **Create new Railway project**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

2. **Configure environment variables**
   ```bash
   # Required variables
   FLASK_ENV=production
   FLASK_DEBUG=False
   DATABASE_URL=mysql://username:password@host:port/database
   STORAGE_TYPE=local
   
   # Optional variables
   PORT=8000
   HOST=0.0.0.0
   ```

3. **Add MySQL database**
   - In Railway dashboard, click "New"
   - Select "Database" → "MySQL"
   - Copy the connection string to `DATABASE_URL`

### Step 3: Deploy

1. **Automatic deployment**
   - Railway will automatically detect the Dockerfile
   - Build and deploy the application
   - Monitor the build logs for any issues

2. **Verify deployment**
   - Check Railway logs for successful startup
   - Test the application URL
   - Verify database connection

### Step 4: Post-Deployment

1. **Initialize database**
   ```bash
   # Access Railway shell
   railway shell
   
   # Run database initialization
   python init_db.py
   ```

2. **Test functionality**
   - Access the application URL
   - Test PDF generation
   - Verify file uploads
   - Check customer ID loading

## 🏠 Local Production Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Nginx (optional, for reverse proxy)

### Step 1: Environment Setup

1. **Create production environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export FLASK_ENV=production
   export FLASK_DEBUG=False
   export DATABASE_URL=mysql://username:password@localhost/garment_db
   export STORAGE_TYPE=local
   ```

### Step 2: Database Setup

1. **Create production database**
   ```sql
   CREATE DATABASE garment_db_prod;
   CREATE USER 'gms_prod'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON garment_db_prod.* TO 'gms_prod'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Initialize database**
   ```bash
   cd backend
   python init_db.py
   ```

### Step 3: Application Setup

1. **Configure WSGI server**
   ```bash
   # Install Gunicorn
   pip install gunicorn
   
   # Start application
   gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
   ```

2. **Set up systemd service** (Linux)
   ```ini
   # /etc/systemd/system/gms.service
   [Unit]
   Description=Garment Management System
   After=network.target
   
   [Service]
   User=www-data
   WorkingDirectory=/path/to/garment_web_app/backend
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   sudo systemctl enable gms
   sudo systemctl start gms
   sudo systemctl status gms
   ```

## 🐳 Docker Deployment

### Step 1: Build Docker Image

1. **Create Dockerfile** (if not using Railway's)
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY backend/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY backend/ .
   COPY frontend/ ../frontend/
   COPY customer_ids.json .
   
   EXPOSE 8000
   
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
   ```

2. **Build image**
   ```bash
   docker build -t garment-management-system .
   ```

### Step 2: Run with Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     app:
       build: .
       ports:
         - "8000:8000"
       environment:
         - FLASK_ENV=production
         - DATABASE_URL=mysql://gms_user:password@db:3306/garment_db
         - STORAGE_TYPE=local
       depends_on:
         - db
       volumes:
         - ./backend/static/uploads:/app/static/uploads
   
     db:
       image: mysql:8.0
       environment:
         - MYSQL_ROOT_PASSWORD=rootpassword
         - MYSQL_DATABASE=garment_db
         - MYSQL_USER=gms_user
         - MYSQL_PASSWORD=password
       volumes:
         - mysql_data:/var/lib/mysql
   
   volumes:
     mysql_data:
   ```

2. **Deploy**
   ```bash
   docker-compose up -d
   ```

## ⚙️ Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `FLASK_DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection | `mysql://user:pass@host:port/db` |
| `STORAGE_TYPE` | Storage service | `local` or `s3` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Application port | `8000` |
| `HOST` | Application host | `0.0.0.0` |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key | - |
| `AWS_S3_BUCKET` | S3 bucket name | - |

### Environment File Example

```bash
# .env (for local development)
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=mysql://GOMS:PGOMS@localhost/garment_db
STORAGE_TYPE=local
PORT=8000
HOST=0.0.0.0
```

## 🗄️ Database Setup

### MySQL Configuration

1. **Create database and user**
   ```sql
   CREATE DATABASE garment_db;
   CREATE USER 'gms_user'@'localhost' IDENTIFIED BY 'secure_password';
   GRANT ALL PRIVILEGES ON garment_db.* TO 'gms_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Configure MySQL settings**
   ```ini
   # /etc/mysql/mysql.conf.d/mysqld.cnf
   [mysqld]
   max_allowed_packet = 64M
   innodb_log_file_size = 256M
   innodb_buffer_pool_size = 1G
   ```

3. **Initialize database schema**
   ```bash
   cd backend
   python init_db.py
   ```

### Database Migration

If you need to migrate from the old Qt application:

1. **Export data from Qt app**
   ```bash
   # Use the migration script (if available)
   python migrate_qt_data.py
   ```

2. **Import customer IDs**
   ```bash
   # Ensure customer_ids.json is properly configured
   curl -X POST http://localhost:8000/api/customers/customer-ids \
     -H "Content-Type: application/json" \
     -d @customer_ids.json
   ```

## 🔍 Troubleshooting

### Common Deployment Issues

#### 1. Database Connection Errors
```bash
# Check database connectivity
mysql -u username -p -h hostname -P port database_name

# Verify environment variables
echo $DATABASE_URL
```

#### 2. PDF Generation Issues
```bash
# Check FPDF installation
python -c "import fpdf; print('FPDF installed')"

# Verify file permissions
ls -la backend/static/uploads/
chmod 755 backend/static/uploads/
```

#### 3. Customer IDs Not Loading
```bash
# Check file path
ls -la backend/customer_ids.json

# Test API endpoint
curl http://localhost:8000/api/customers/customer-ids
```

#### 4. Railway Build Failures
```bash
# Check build logs in Railway dashboard
# Common issues:
# - Missing dependencies in requirements.txt
# - Incorrect file paths
# - Environment variable issues
```

### Log Analysis

#### Railway Logs
```bash
# View Railway logs
railway logs

# Filter for errors
railway logs | grep ERROR
```

#### Application Logs
```bash
# Check application logs
tail -f backend/backend.log

# Check system logs (Linux)
sudo journalctl -u gms -f
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_customer_id ON customers(customer_id);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_packing_list_serial ON packing_lists(packing_list_serial);
```

#### 2. Application Optimization
```python
# Enable database connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

#### 3. Static File Optimization
```bash
# Compress static files
gzip -9 backend/static/uploads/*.pdf
gzip -9 backend/static/uploads/*.jpg
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Use HTTPS in production
- [ ] Set secure database passwords
- [ ] Configure proper file permissions
- [ ] Enable database connection encryption
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Backup strategy implementation
- [ ] Monitor application logs

### SSL/TLS Configuration

#### Nginx SSL Configuration
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoring and Maintenance

### Health Checks

1. **Application health endpoint**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Database connectivity**
   ```bash
   curl http://localhost:8000/api/test
   ```

### Backup Strategy

1. **Database backup**
   ```bash
   # Daily backup script
   mysqldump -u username -p database_name > backup_$(date +%Y%m%d).sql
   ```

2. **File backup**
   ```bash
   # Backup uploads directory
   tar -czf uploads_backup_$(date +%Y%m%d).tar.gz backend/static/uploads/
   ```

### Update Process

1. **Code updates**
   ```bash
   git pull origin main
   pip install -r backend/requirements.txt
   python init_db.py  # If schema changes
   systemctl restart gms
   ```

2. **Dependency updates**
   ```bash
   pip install --upgrade -r backend/requirements.txt
   ```

---

**Last Updated**: August 2025  
**Version**: 2.0.0  
**Status**: Production Ready
