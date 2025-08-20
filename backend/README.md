# Garment Management System - Backend

This is the Flask backend for the Garment Management System web application.

## Features

- **Fabric Invoice Management**: Manage fabric invoices and line items
- **Stitching Records**: Create and manage stitching records with multi-fabric support
- **Packing Lists**: Generate and manage packing lists
- **Group Bills**: Create group billing with PDF generation
- **File Management**: Handle image uploads and PDF generation
- **RESTful API**: Complete API for frontend integration

## Database Models

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

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `env.example` to `.env` and configure your environment variables:

```bash
cp env.example .env
```

### 3. Database Setup

Make sure you have MySQL running and create the database:

```sql
CREATE DATABASE garment_db;
CREATE USER 'GOMS'@'localhost' IDENTIFIED BY 'PGOMS';
GRANT ALL PRIVILEGES ON garment_db.* TO 'GOMS'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Run the Application

```bash
python app.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /api/health` - Check API status

### Fabric Invoices
- `GET /api/invoices` - Get all invoices
- `POST /api/invoices` - Create new invoice
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice
- `POST /api/invoices/import-dat` - Import .dat file

### Stitching Records
- `GET /api/stitching` - Get all stitching records
- `POST /api/stitching` - Create new stitching record
- `PUT /api/stitching/{id}` - Update stitching record
- `DELETE /api/stitching/{id}` - Delete stitching record

### Packing Lists
- `GET /api/packing-lists` - Get all packing lists
- `POST /api/packing-lists` - Create new packing list
- `PUT /api/packing-lists/{id}` - Update packing list
- `DELETE /api/packing-lists/{id}` - Delete packing list

### Group Bills
- `GET /api/group-bills` - Get all group bills
- `POST /api/group-bills` - Create new group bill
- `DELETE /api/group-bills/{id}` - Delete group bill

### File Operations
- `POST /api/files/upload-image` - Upload garment image
- `GET /api/files/download-pdf/{type}/{id}` - Download PDF

## Deployment

### Railway.app Deployment

1. Push your code to GitHub
2. Connect your repository to Railway.app
3. Add MySQL database service
4. Set environment variables in Railway dashboard
5. Deploy

### Environment Variables for Production

- `DATABASE_URL` - Railway MySQL connection string
- `SECRET_KEY` - Flask secret key
- `FLASK_DEBUG` - Set to False for production

## Development

### Project Structure

```
backend/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── config/              # Configuration files
├── static/              # Static files (uploads, PDFs, images)
├── templates/           # HTML templates (if needed)
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
└── Dockerfile          # Docker configuration
```

### Adding New Features

1. Create models in `app/models/`
2. Create routes in `app/routes/`
3. Add business logic in `app/services/`
4. Update the main app.py to register new blueprints

## Database Migration

To migrate from the existing Qt application:

1. Export data from existing MySQL database
2. Import into new database structure
3. Verify data integrity
4. Update any missing relationships

## Testing

Run tests with:

```bash
python -m pytest tests/
```

## License

This project is part of the Garment Management System.
