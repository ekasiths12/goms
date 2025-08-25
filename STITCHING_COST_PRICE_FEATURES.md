# Stitching Cost and Price Tracking Features

This document describes the new stitching cost and price tracking features implemented in the ERP system.

## Overview

The stitching cost and price tracking system allows users to:
- Memorize stitching costs by garment and location combination
- Memorize stitching prices by garment and customer combination
- Auto-populate costs and prices when creating new stitching records
- View and manage cost and price lists
- Track stitching profit (price - cost) instead of just revenue

## Database Changes

### New Tables

1. **stitching_costs** - Stores memorized costs by garment and location
   - `id` (Primary Key)
   - `garment_name` (VARCHAR)
   - `stitching_location` (VARCHAR)
   - `cost` (DECIMAL)
   - `created_at` (DATETIME)
   - `updated_at` (DATETIME)
   - Unique constraint on (garment_name, stitching_location)

2. **stitching_prices** - Stores memorized prices by garment and customer
   - `id` (Primary Key)
   - `garment_name` (VARCHAR)
   - `customer_id` (Foreign Key to customers.id)
   - `price` (DECIMAL)
   - `created_at` (DATETIME)
   - `updated_at` (DATETIME)
   - Unique constraint on (garment_name, customer_id)

### Modified Tables

1. **stitching_invoices** - Added new field
   - `stitching_cost` (DECIMAL) - Stores the cost for each stitching record

## API Endpoints

### Cost List Management

- `GET /api/cost-price/costs` - Get all costs with optional filtering
- `POST /api/cost-price/costs` - Create a new cost entry
- `PUT /api/cost-price/costs/{id}` - Update an existing cost
- `DELETE /api/cost-price/costs/{id}` - Delete a cost entry
- `GET /api/cost-price/costs/auto-populate` - Get memorized cost for garment/location

### Price List Management

- `GET /api/cost-price/prices` - Get all prices with optional filtering
- `POST /api/cost-price/prices` - Create a new price entry
- `PUT /api/cost-price/prices/{id}` - Update an existing price
- `DELETE /api/cost-price/prices/{id}` - Delete a price entry
- `GET /api/cost-price/prices/auto-populate` - Get memorized price for garment/customer

### Stitching Auto-Population

- `GET /api/stitching/auto-populate-cost` - Get cost for stitching record creation
- `GET /api/stitching/auto-populate-price` - Get price for stitching record creation

## Frontend Features

### Cost List and Price List Tables

Located in the Fabric Invoices page, accessible via navigation tabs:
- **Cost List Tab** - View and manage stitching costs
- **Price List Tab** - View and manage stitching prices

#### Features:
- Filter by garment name and location/customer
- Add new cost/price entries
- Edit existing entries
- Delete entries
- Real-time filtering with debounced search

### Dashboard Updates

The dashboard now shows:
- **Total Profit** instead of Total Revenue
- **Stitching Profit** (price - cost) instead of Stitching Revenue
- **Stitching Cost** for reference
- All charts and metrics updated to reflect profit calculations

## Usage Instructions

### Setting Up Costs and Prices

1. Navigate to the Fabric Invoices page
2. Click on "Cost List" or "Price List" tab
3. Click "Add New Cost" or "Add New Price"
4. Fill in the required fields:
   - **Cost**: Garment name, stitching location, cost amount
   - **Price**: Garment name, customer, price amount
5. Save the entry

### Auto-Population in Stitching Records

When creating a new stitching record:
1. The system will automatically check for memorized costs based on:
   - Garment name (stitched_item)
   - Stitching location (delivered_location from invoice line)
2. The system will automatically check for memorized prices based on:
   - Garment name (stitched_item)
   - Customer ID (from invoice line)
3. If found, the cost and price fields will be auto-populated
4. Users can still edit these values if needed

### Viewing Profit Data

1. Navigate to the Dashboard
2. All revenue metrics now show profit calculations
3. Stitching profit = Stitching price - Stitching cost
4. Total profit includes fabric commission + stitching profit + direct commission

## Database Migration

To apply the database changes, run the migration script:

```bash
cd backend
python migrations/add_stitching_cost_price_tables.py
```

## Testing

Run the test script to verify all functionality:

```bash
cd backend
python test_stitching_cost_price.py
```

## Technical Notes

### Auto-Population Logic

The auto-population works as follows:
1. When creating a stitching record, the system extracts:
   - Garment name from `stitched_item` field
   - Stitching location from `delivered_location` in the associated invoice line
   - Customer ID from the invoice line's customer relationship
2. The system queries the memorization tables for matching entries
3. If found, the values are auto-populated in the form
4. Users can override these values if needed

### Profit Calculation

Profit is calculated as:
- **Stitching Profit** = Stitching Price - Stitching Cost
- **Total Profit** = Fabric Commission + Stitching Profit + Direct Commission

### Data Validation

- All cost and price values must be positive numbers
- Garment names and locations are case-sensitive for matching
- Customer IDs must exist in the customers table
- Unique constraints prevent duplicate entries for the same garment/location or garment/customer combinations

## Future Enhancements

Potential improvements for future versions:
1. Bulk import/export of cost and price data
2. Cost and price history tracking
3. Profit margin percentage calculations
4. Cost and price trend analysis
5. Integration with accounting systems
6. Advanced filtering and reporting options
