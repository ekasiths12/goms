# Garment Management System

A comprehensive web application for managing garment manufacturing processes, including fabric invoices, stitching records, packing lists, and group bills.

## 🏗️ Project Structure

```
garment_web_app/
├── backend/                 # Flask backend application
│   ├── app/                # Application modules
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── config/             # Configuration files
│   ├── static/             # Static files (images, PDFs)
│   ├── templates/          # HTML templates
│   ├── main.py            # Flask application factory
│   ├── wsgi.py            # WSGI entry point
│   └── requirements.txt   # Python dependencies
├── frontend/               # Frontend HTML files
│   ├── fabric-invoices.html
│   ├── stitching-records.html
│   ├── packing-lists.html
│   ├── group-bills.html
│   └── login.html
├── qt-desktop-app/         # Qt desktop application
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── tests/                  # Test files
```

## 🚀 Quick Start

### Local Development

1. **Start Backend:**
   ```bash
   python3 run_local.py
   ```

2. **Start Frontend (optional):**
   ```bash
   python3 serve_frontend.py
   ```

3. **Access Application:**
   - Backend: http://localhost:8000
   - Frontend: http://localhost:3000

### Production Deployment

The application is configured for Railway deployment:

1. Push to GitHub
2. Connect repository to Railway
3. Add MySQL database service
4. Deploy automatically

## 📋 Features

- **Fabric Invoice Management** - Track fabric purchases and consumption
- **Stitching Records** - Manage garment stitching with image uploads
- **Packing Lists** - Generate delivery packing lists with costs
- **Group Bills** - Create consolidated billing groups
- **PDF Generation** - Automatic PDF reports with images
- **File Storage** - Railway volume storage for images and PDFs

## 🛠️ Technology Stack

- **Backend:** Flask, SQLAlchemy, MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Desktop:** Qt (Python)
- **Deployment:** Railway
- **Storage:** Railway Volumes

## 📁 Key Files

- `run_local.py` - Local development server
- `serve_frontend.py` - Frontend development server
- `backend/main.py` - Flask application factory
- `backend/start.py` - Railway startup script
- `railway.json` - Railway deployment configuration

## 🔧 Configuration

Environment variables:
- `DATABASE_URL` - MySQL connection string
- `RAILWAY_VOLUME_PATH` - File storage path
- `FLASK_ENV` - Environment (development/production)

## 📝 License

This project is proprietary software for garment manufacturing management.
