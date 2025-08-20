# Garment Management System - Web Application

This is the web-based version of the Garment Management System, converted from the original Qt desktop application.

## 🚀 Project Overview

The Garment Management System is a comprehensive solution for managing garment manufacturing operations including:

- **Fabric Invoice Management**: Import and manage fabric invoices with .dat file support
- **Stitching Records**: Create and track stitching records with multi-fabric support
- **Packing Lists**: Generate packing lists for deliveries
- **Group Bills**: Create group billing with PDF generation
- **File Management**: Handle image uploads and PDF downloads

## 📁 Project Structure

```
garment_web_app/
├── backend/                 # Flask API backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── config/             # Configuration files
│   ├── static/             # Static files (uploads, PDFs, images)
│   ├── app.py             # Main Flask application
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Docker configuration
│   └── README.md          # Backend documentation
├── frontend/               # Frontend application
│   ├── index.html         # Main HTML file with navigation
│   └── README.md          # Frontend documentation
└── README.md              # This file
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **File Handling**: FPDF for PDF generation
- **Deployment**: Railway.app with Docker

### Frontend
- **Framework**: Vanilla JavaScript with HTML5/CSS3
- **UI**: Modern dark theme with responsive design
- **Navigation**: Fixed top navigation tabs
- **API Integration**: RESTful API calls

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Git

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd garment_web_app/backend
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your database credentials
   ```

4. **Initialize database**:
   ```bash
   python init_db.py
   ```

5. **Run the backend**:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd garment_web_app/frontend
   ```

2. **Open in browser**:
   ```bash
   open index.html
   # Or simply double-click the file
   ```

## 🧪 Testing

### Backend Testing
```bash
cd garment_web_app/backend
python test_setup.py
```

### API Endpoints Testing
- Health Check: `GET /api/health`
- Customers: `GET /api/customers`
- Invoices: `GET /api/invoices` (TODO)
- Stitching: `GET /api/stitching` (TODO)
- Packing Lists: `GET /api/packing-lists` (TODO)
- Group Bills: `GET /api/group-bills` (TODO)

## 📊 Database Schema

### Core Tables
- `customers` - Customer information
- `invoices` - Fabric invoice headers
- `invoice_lines` - Individual invoice line items
- `stitching_invoices` - Stitching records
- `garment_fabrics` - Multi-fabric support
- `lining_fabrics` - Lining fabric details
- `packing_lists` - Packing list management
- `packing_list_lines` - Packing list items
- `stitching_invoice_groups` - Group billing
- `stitching_invoice_group_lines` - Group billing items
- `images` - Garment images
- `serial_counters` - Serial number management

## 🚀 Deployment

### Railway.app Deployment

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial web application setup"
   git push origin main
   ```

2. **Connect to Railway.app**:
   - Go to [Railway.app](https://railway.app)
   - Connect your GitHub repository
   - Add MySQL database service
   - Set environment variables

3. **Environment Variables**:
   ```
   DATABASE_URL=mysql://username:password@host:port/database
   SECRET_KEY=your-secret-key
   FLASK_DEBUG=False
   ```

4. **Deploy**:
   - Railway will automatically deploy from your main branch
   - The application will be available at your Railway URL

## 🔄 Migration from Qt Application

### Data Migration Steps

1. **Export existing data**:
   ```sql
   mysqldump -u GOMS -p garment_db > garment_db_backup.sql
   ```

2. **Import to new database**:
   ```sql
   mysql -u GOMS -p garment_db_new < garment_db_backup.sql
   ```

3. **Verify data integrity**:
   - Check all relationships
   - Verify serial numbers
   - Test PDF generation

### File Migration

1. **Copy static files**:
   ```bash
   cp -r ../images/* garment_web_app/backend/static/images/
   cp -r ../packing_lists/* garment_web_app/backend/static/pdfs/
   cp -r ../group_bills/* garment_web_app/backend/static/pdfs/
   ```

2. **Update file paths in database**:
   - Update image paths in `images` table
   - Update PDF paths in relevant tables

## 📋 Development Roadmap

### Phase 1: Backend Foundation ✅
- [x] Flask application setup
- [x] Database models
- [x] Basic API routes
- [x] Customer management
- [x] Docker configuration

### Phase 2: Core Features 🚧
- [ ] Fabric invoice management
- [ ] .dat file import functionality
- [ ] Stitching record creation
- [ ] Multi-fabric support
- [ ] Image upload handling

### Phase 3: Advanced Features 📋
- [ ] Packing list generation
- [ ] Group bill creation
- [ ] PDF generation
- [ ] File management
- [ ] Search and filtering

### Phase 4: Frontend Enhancement 📋
- [ ] React/Vue.js frontend
- [ ] Advanced UI components
- [ ] Real-time updates
- [ ] Mobile responsiveness

### Phase 5: Production Features 📋
- [ ] User authentication
- [ ] Role-based access
- [ ] Audit logging
- [ ] Performance optimization
- [ ] Monitoring and analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is part of the Garment Management System.

## 🆘 Support

For support and questions:
- Check the documentation in each directory
- Review the API endpoints
- Test with the provided test scripts

---

**Status**: Backend foundation complete, ready for feature development
