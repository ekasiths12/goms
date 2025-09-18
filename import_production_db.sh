#!/bin/bash

# Database Import Script for Railway Production to Local Development
# This script imports the database from Railway production environment
# and overwrites the local development database.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Railway production database configuration
RAILWAY_HOST="shortline.proxy.rlwy.net"
RAILWAY_PORT="43260"
RAILWAY_USER="root"
RAILWAY_PASSWORD="GfXdBdQdvLYFhQDjOHDwurszAkmVxLjF"
RAILWAY_DATABASE="railway"

# Local development database configuration
LOCAL_HOST="localhost"
LOCAL_PORT="3306"
LOCAL_USER="GOMS"
LOCAL_PASSWORD="PGOMS"
LOCAL_DATABASE="garment_db"

# Generate timestamp for backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_garment_db_${TIMESTAMP}.sql"
TEMP_SQL_FILE=$(mktemp /tmp/railway_export_XXXXXX.sql)

echo -e "${BLUE}🚀 Starting database import from Railway production...${NC}"
echo "============================================================"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}💡 $1${NC}"
}

# Check if required tools are available
check_requirements() {
    echo "🔍 Checking requirements..."
    
    if ! command -v mysqldump &> /dev/null; then
        print_error "mysqldump not found. Please install MySQL client tools."
        exit 1
    fi
    
    if ! command -v mysql &> /dev/null; then
        print_error "mysql client not found. Please install MySQL client tools."
        exit 1
    fi
    
    print_success "MySQL client tools found"
}

# Test Railway database connection
test_railway_connection() {
    echo "🔗 Testing Railway database connection..."
    
    if mysql -h "$RAILWAY_HOST" -P "$RAILWAY_PORT" -u "$RAILWAY_USER" -p"$RAILWAY_PASSWORD" -e "SELECT 1;" "$RAILWAY_DATABASE" &> /dev/null; then
        print_success "Railway database connection successful"
    else
        print_error "Railway database connection failed"
        print_info "Make sure you have internet connection and Railway database is accessible"
        exit 1
    fi
}

# Test local database connection
test_local_connection() {
    echo "🔗 Testing local database connection..."
    
    if mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" -e "SELECT 1;" "$LOCAL_DATABASE" &> /dev/null; then
        print_success "Local database connection successful"
    else
        print_error "Local database connection failed"
        print_info "Make sure your local MySQL server is running and the '$LOCAL_DATABASE' database exists"
        exit 1
    fi
}

# Create backup of local database
create_backup() {
    echo "💾 Creating backup of local database..."
    
    if mysqldump -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" \
        --single-transaction --routines --triggers "$LOCAL_DATABASE" > "$BACKUP_FILE"; then
        print_success "Local database backed up to: $BACKUP_FILE"
    else
        print_error "Failed to create backup"
        exit 1
    fi
}

# Export database from Railway
export_railway_database() {
    echo "📤 Exporting database from Railway..."
    
    if mysqldump -h "$RAILWAY_HOST" -P "$RAILWAY_PORT" -u "$RAILWAY_USER" -p"$RAILWAY_PASSWORD" \
        --single-transaction --routines --triggers --set-gtid-purged=OFF "$RAILWAY_DATABASE" > "$TEMP_SQL_FILE"; then
        print_success "Railway database exported successfully"
    else
        print_error "Failed to export from Railway"
        exit 1
    fi
}

# Clear local database
clear_local_database() {
    echo "🗑️  Clearing local database..."
    
    mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DATABASE" << EOF
SET FOREIGN_KEY_CHECKS = 0;
$(mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" -N -e "SELECT CONCAT('DROP TABLE IF EXISTS \`', table_name, '\`;') FROM information_schema.tables WHERE table_schema = '$LOCAL_DATABASE';" "$LOCAL_DATABASE")
SET FOREIGN_KEY_CHECKS = 1;
EOF
    
    print_success "Local database cleared"
}

# Import to local database
import_to_local_database() {
    echo "📥 Importing data to local database..."
    
    if mysql -h "$LOCAL_HOST" -P "$LOCAL_PORT" -u "$LOCAL_USER" -p"$LOCAL_PASSWORD" "$LOCAL_DATABASE" < "$TEMP_SQL_FILE"; then
        print_success "Data imported successfully to local database"
    else
        print_error "Failed to import to local database"
        print_info "You can restore from backup: $BACKUP_FILE"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    if [ -f "$TEMP_SQL_FILE" ]; then
        rm -f "$TEMP_SQL_FILE"
        echo "🧹 Cleaned up temporary files"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    # Check requirements
    check_requirements
    
    # Test connections
    test_railway_connection
    test_local_connection
    
    # Confirm with user
    echo ""
    print_warning "This will completely overwrite your local database!"
    echo "   Local database: $LOCAL_DATABASE"
    echo "   Railway database: $RAILWAY_DATABASE"
    echo ""
    read -p "Do you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]] && [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Operation cancelled by user"
        exit 0
    fi
    
    # Execute the import process
    create_backup
    export_railway_database
    clear_local_database
    import_to_local_database
    
    echo ""
    echo "============================================================"
    print_success "Database import completed successfully!"
    echo "📁 Backup saved as: $BACKUP_FILE"
    print_info "Your local database now contains the production data"
}

# Run main function
main "$@"
