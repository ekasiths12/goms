# 🏭 Garment Management System (GMS)

A modern web-based garment management system built with Flask and vanilla JavaScript, designed to replace the legacy Qt desktop application.

## 📋 Features

### 🧵 Core Functionality
- **Customer Management**: Add, edit, and manage customer information
- **Invoice Management**: Create and manage fabric and stitching invoices
- **Packing Lists**: Generate detailed packing lists with garment specifications
- **Group Bills**: Organize invoices into logical groups for billing
- **PDF Generation**: Generate professional PDF reports for invoices and packing lists
- **Image Management**: Upload and associate images with garments
- **Data Import**: Import data from legacy .dat files with customer ID filtering

### 📊 Reports & PDFs
- **Stitching Invoice PDFs**: Professional invoices with tax calculations
- **Fabric Used PDFs**: Detailed fabric consumption reports
- **Packing List PDFs**: Comprehensive garment specifications
- **Group Bill PDFs**: Consolidated billing documents

### 🎨 Modern UI
- **Dark Theme**: Professional dark interface
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic data loading and updates
- **Expandable Rows**: Hierarchical data display for fabrics and linings

## 🏗️ Architecture

### Backend (Flask)
```
backend/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── config/              # Configuration files
├── static/              # Static assets
└── main.py             # Flask application entry point
```

### Frontend (Vanilla JavaScript)
```
frontend/
├── fabric-invoices.html    # Fabric invoice management
├── group-bills.html        # Group bill management
├── packing-lists.html      # Packing list management
├── stitching-records.html  # Stitching record management
├── login.html             # Authentication
└── index.html             # Landing page
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd garment_web_app
   ```

2. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE garment_db;
   CREATE USER 'GOMS'@'localhost' IDENTIFIED BY 'PGOMS';
   GRANT ALL PRIVILEGES ON garment_db.* TO 'GOMS'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. **Initialize database**
   ```bash
   python init_db.py
   ```

5. **Start development server**
   ```bash
   python run_local.py
   ```

6. **Access the application**
   - Backend API: http://localhost:8000
   - Frontend: Open `frontend/fabric-invoices.html` in your browser

## 📁 Project Structure

```
garment_web_app/
├── backend/                 # Flask backend application
│   ├── app/                # Main application package
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes and endpoints
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── config/             # Configuration files
│   ├── static/             # Static assets (uploads, images)
│   ├── main.py            # Flask app entry point
│   ├── wsgi.py            # WSGI entry point for production
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile.railway # Railway deployment configuration
├── frontend/               # Frontend HTML/JS files
│   ├── fabric-invoices.html
│   ├── group-bills.html
│   ├── packing-lists.html
│   ├── stitching-records.html
│   ├── login.html
│   └── index.html
├── run_local.py           # Local development script
├── serve_frontend.py      # Frontend server script
├── customer_ids.json      # Customer ID configuration
├── railway.json           # Railway deployment config
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables
- `FLASK_DEBUG`: Enable debug mode (True/False)
- `FLASK_ENV`: Environment (development/production)
- `DATABASE_URL`: Database connection string
- `STORAGE_TYPE`: Storage service type (local/s3)

### Customer IDs Configuration
The `customer_ids.json` file contains customer IDs for data import filtering:
```json
["280", "322", "325", "327", "328", "332", "355", "360", "362", "363", "365", "371", "375", "384", "387", "396", "397", "398", "410", "416", "425", "429", "430", "433", "441", "451", "454"]
```

## 📚 API Documentation

### Core Endpoints
- `GET /api/customers` - Get all customers
- `POST /api/customers` - Create new customer
- `GET /api/invoices` - Get all invoices
- `POST /api/invoices` - Create new invoice
- `GET /api/packing-lists` - Get all packing lists
- `POST /api/packing-lists` - Create new packing list
- `GET /api/group-bills` - Get all group bills
- `POST /api/group-bills` - Create new group bill

### PDF Generation Endpoints
- `GET /api/packing-lists/{id}/pdf` - Generate packing list PDF
- `GET /api/group-bills/{id}/stitching-pdf` - Generate stitching invoice PDF
- `GET /api/group-bills/{id}/fabric-pdf` - Generate fabric used PDF

### Data Import Endpoints
- `POST /api/import/dat` - Import data from .dat files
- `GET /api/customers/customer-ids` - Get customer ID filter
- `POST /api/customers/customer-ids` - Update customer ID filter

## 🗄️ Database Schema

### Core Tables
- `customers` - Customer information
- `invoices` - Invoice records
- `invoice_lines` - Invoice line items
- `stitching_invoices` - Stitching invoice details
- `stitching_invoice_groups` - Grouped stitching invoices
- `packing_lists` - Packing list records
- `packing_list_lines` - Packing list line items
- `images` - Uploaded garment images
- `garment_fabrics` - Primary fabric details
- `lining_fabrics` - Lining fabric details

## 🚀 Deployment

### Railway Deployment
The application is configured for Railway deployment with:
- `railway.json` - Railway configuration
- `Dockerfile.railway` - Docker configuration
- `wsgi.py` - WSGI entry point

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🛠️ Development

### Development Scripts
- `run_local.py` - Start local development server
- `serve_frontend.py` - Serve frontend files locally
- `backend/start.py` - Alternative backend start script
- `backend/railway_start.py` - Railway-specific start script
- `backend/init_db.py` - Database initialization

### Code Style
- Python: PEP 8 compliant
- JavaScript: ES6+ with modern practices
- HTML: Semantic HTML5
- CSS: Modern CSS with flexbox/grid

## 🔍 Troubleshooting

### Common Issues
1. **Database Connection**: Ensure MySQL is running and credentials are correct
2. **PDF Generation**: Check FPDF installation and file permissions
3. **Image Uploads**: Verify upload directory permissions
4. **Customer IDs**: Ensure `customer_ids.json` is properly formatted

### Debug Mode
Enable debug mode by setting `FLASK_DEBUG=True` in environment variables.

## 📄 License

This project is proprietary software developed for internal use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For support and questions, contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: August 2025  
**Status**: Production Ready
