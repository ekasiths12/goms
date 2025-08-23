# Customer ID Mapping System Changes

## Overview
The customer ID system has been updated to store customer IDs in a database table instead of a JSON file, and now includes automatic matching of customer IDs with short names from .dat file imports.

## Changes Made

### 1. New Database Model
- **File**: `backend/app/models/customer_id_mapping.py`
- **Purpose**: Stores customer ID mappings with short names
- **Fields**:
  - `id`: Primary key
  - `customer_id`: Unique customer ID (string)
  - `short_name`: Customer short name (nullable)
  - `created_at`: Timestamp when record was created
  - `updated_at`: Timestamp when record was last updated

### 2. Updated Backend Routes
- **File**: `backend/app/routes/customers.py`
- **Changes**:
  - Updated `/api/customers/customer-ids` GET endpoint to read from database instead of JSON file
  - Updated `/api/customers/customer-ids` POST endpoint to save to database instead of JSON file
  - Added new `/api/customers/customer-id-mappings` GET endpoint to return mappings with short names

### 3. Enhanced .dat File Import
- **File**: `backend/app/routes/files.py`
- **Changes**:
  - Added automatic creation/update of customer ID mappings during .dat file import
  - Customer short names are now stored when first encountered in .dat files
  - Only updates short names if they are currently empty (preserves existing data)

### 4. Updated Frontend Dialog
- **File**: `frontend/fabric-invoices.html`
- **Changes**:
  - Customer ID dialog now shows both customer ID and short name
  - Added loading of customer ID mappings with short names
  - Enhanced display to show customer names alongside IDs
  - Improved visual layout with flexbox for better alignment

## Key Features

### Automatic Short Name Matching
- When a .dat file is imported, customer IDs are automatically matched with their short names
- Short names are only updated if they are currently empty
- This ensures data consistency and prevents overwriting existing information

### Database Storage
- All customer ID mappings are now stored in the database
- No more dependency on JSON files
- Better data integrity and consistency

### Enhanced User Interface
- Customer ID dialog now displays both ID and name
- Users can see which customer IDs have associated names
- Better visual organization of information

## Migration
- Existing customer IDs from `customer_ids.json` have been migrated to the database
- All 27 customer IDs were successfully migrated
- The system is backward compatible with existing functionality

## API Endpoints

### GET `/api/customers/customer-ids`
Returns a list of customer IDs (for backward compatibility)

### POST `/api/customers/customer-ids`
Saves customer IDs to the database

### GET `/api/customers/customer-id-mappings`
Returns customer ID mappings with short names:
```json
[
  {
    "id": 1,
    "customer_id": "280",
    "short_name": "Customer Name",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

## Usage

### Adding Customer IDs
1. Open the Customer IDs dialog in the fabric invoices page
2. Enter a customer ID and click "Add"
3. The customer ID will be stored in the database

### Importing .dat Files
1. When importing a .dat file, customer IDs are automatically processed
2. If a customer ID doesn't exist, it's created with the short name from the .dat file
3. If a customer ID exists but has no short name, the short name is added
4. If a customer ID exists and has a short name, it's preserved

### Viewing Customer Information
- The Customer IDs dialog now shows both customer IDs and their associated short names
- Customer names appear in blue text next to the customer IDs
- "No name" is displayed for customer IDs without associated short names

## Benefits
1. **Data Consistency**: All customer information is stored in the database
2. **Automatic Matching**: Customer IDs are automatically matched with names during import
3. **Better UX**: Users can see customer names in the dialog
4. **Scalability**: Database storage is more scalable than JSON files
5. **Data Integrity**: Better handling of data relationships and constraints
