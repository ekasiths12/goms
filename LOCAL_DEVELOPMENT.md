# Local Development Setup

This guide will help you run the Garment Management System locally for testing without waiting for Railway deployment.

## 🚀 Quick Start

### Option 1: Use the provided scripts (Recommended)

1. **Start the Flask Backend:**
   ```bash
   python run_local.py
   ```

2. **Start the Frontend Server (in a new terminal):**
   ```bash
   python serve_frontend.py
   ```

3. **Open your browser:**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000/fabric-invoices.html

### Option 2: Manual setup

1. **Install dependencies:**
   ```bash
   pip install flask flask-sqlalchemy flask-cors pymysql python-dotenv
   ```

2. **Start Flask backend:**
   ```bash
   cd backend
   python main.py
   ```

3. **Serve frontend files:**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

## 📋 Prerequisites

### Database Setup
You need a local MySQL database running. The app expects:
- **Database name:** `garment_db`
- **Username:** `GOMS`
- **Password:** `PGOMS`
- **Host:** `localhost`
- **Port:** `3306` (default)

### MySQL Installation (if not installed)

**On macOS:**
```bash
# Using Homebrew
brew install mysql
brew services start mysql

# Create database and user
mysql -u root -p
CREATE DATABASE garment_db;
CREATE USER 'GOMS'@'localhost' IDENTIFIED BY 'PGOMS';
GRANT ALL PRIVILEGES ON garment_db.* TO 'GOMS'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**On Windows:**
1. Download MySQL from https://dev.mysql.com/downloads/mysql/
2. Install and follow the setup wizard
3. Use MySQL Workbench or command line to create the database and user

**On Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
sudo mysql -u root -p
CREATE DATABASE garment_db;
CREATE USER 'GOMS'@'localhost' IDENTIFIED BY 'PGOMS';
GRANT ALL PRIVILEGES ON garment_db.* TO 'GOMS'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 🔧 Configuration

### Environment Variables
The app uses these environment variables (automatically set by `run_local.py`):

```bash
FLASK_DEBUG=True
FLASK_ENV=development
DATABASE_URL=mysql://GOMS:PGOMS@localhost/garment_db
```

### Database Initialization
After starting the backend, initialize the database:
- Visit: http://localhost:8000/api/init-db
- This will create all necessary tables

## 🌐 Access Points

### Backend (Flask API)
- **Main API:** http://localhost:8000
- **Health Check:** http://localhost:8000/api/health
- **Test Endpoint:** http://localhost:8000/test
- **Database Init:** http://localhost:8000/api/init-db

### Frontend (HTML Pages)
- **Fabric Invoices:** http://localhost:3000/fabric-invoices.html
- **Stitching Records:** http://localhost:3000/stitching-records.html
- **Packing Lists:** http://localhost:3000/packing-lists.html
- **Group Bills:** http://localhost:3000/group-bills.html
- **Dashboard:** http://localhost:3000/index.html

## 🧪 Testing Workflow

1. **Make changes** to your code
2. **Save the files** - Flask will auto-reload (debug mode)
3. **Refresh your browser** to see changes
4. **Test functionality** immediately
5. **No need to wait** for Railway deployment!

## 🔍 Debugging

### Backend Issues
- Check Flask console output for errors
- Visit http://localhost:8000/api/health for database status
- Check MySQL is running: `brew services list` (macOS) or `systemctl status mysql` (Linux)

### Frontend Issues
- Open browser Developer Tools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for API call failures

### Common Issues

**Database Connection Error:**
```
OperationalError: (2003, "Can't connect to MySQL server")
```
- Make sure MySQL is running
- Check database credentials in config
- Verify database exists

**Port Already in Use:**
```
OSError: [Errno 48] Address already in use
```
- Kill existing processes: `lsof -ti:8000 | xargs kill -9`
- Or use different ports

**Module Not Found:**
```
ModuleNotFoundError: No module named 'flask'
```
- Install dependencies: `pip install -r requirements.txt`

## 📁 Project Structure

```
garment_web_app/
├── backend/                 # Flask backend
│   ├── main.py             # Flask app entry point
│   ├── app/                # Application code
│   │   ├── routes/         # API routes
│   │   ├── models/         # Database models
│   │   └── ...
│   └── config/             # Configuration
├── frontend/               # HTML/CSS/JS files
│   ├── fabric-invoices.html
│   ├── stitching-records.html
│   └── ...
├── run_local.py           # Backend startup script
├── serve_frontend.py      # Frontend server script
└── LOCAL_DEVELOPMENT.md   # This file
```

## 🚀 Production vs Development

| Feature | Development (Local) | Production (Railway) |
|---------|-------------------|---------------------|
| Database | Local MySQL | Railway MySQL |
| Debug Mode | Enabled | Disabled |
| HTTPS | Disabled | Enabled |
| Auto-reload | Yes | No |
| Environment | Local | Railway |

## 💡 Tips

1. **Keep both servers running** while developing
2. **Use browser dev tools** for debugging
3. **Check Flask console** for backend errors
4. **Test API endpoints** directly in browser
5. **Commit changes** when working correctly
6. **Push to GitHub** to deploy to Railway

## 🆘 Troubleshooting

If you encounter issues:

1. **Check MySQL status:**
   ```bash
   brew services list | grep mysql  # macOS
   systemctl status mysql          # Linux
   ```

2. **Reset database:**
   ```bash
   mysql -u GOMS -p garment_db
   DROP DATABASE garment_db;
   CREATE DATABASE garment_db;
   EXIT;
   ```
   Then visit http://localhost:8000/api/init-db

3. **Clear browser cache** and refresh

4. **Check ports are free:**
   ```bash
   lsof -i :8000  # Check port 8000
   lsof -i :3000  # Check port 3000
   ```

Happy coding! 🎉
