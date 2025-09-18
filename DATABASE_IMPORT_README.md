# Database Import Scripts

This directory contains scripts to import the production database from Railway.app to your local development environment.

## Available Scripts

### 1. Python Script (`import_production_db.py`)
A comprehensive Python script with detailed error handling and progress reporting.

**Usage:**
```bash
python import_production_db.py
```

**Features:**
- ✅ Connection testing for both databases
- ✅ Automatic backup creation before import
- ✅ Detailed progress reporting
- ✅ Error handling and rollback information
- ✅ Temporary file cleanup

### 2. Shell Script (`import_production_db.sh`)
A faster shell script version using native MySQL tools.

**Usage:**
```bash
./import_production_db.sh
```

**Features:**
- ✅ Faster execution using native MySQL tools
- ✅ Colored output for better readability
- ✅ Automatic backup creation
- ✅ Connection testing

## Prerequisites

### Required Tools
- **MySQL Client Tools**: `mysqldump` and `mysql` command-line tools
- **Python Dependencies** (for Python script): `PyMySQL`, `python-dotenv`

### Install MySQL Client Tools

**macOS (using Homebrew):**
```bash
brew install mysql-client
```

**Ubuntu/Debian:**
```bash
sudo apt-get install mysql-client
```

**Windows:**
Download and install MySQL Workbench or MySQL Command Line Client.

### Install Python Dependencies
```bash
pip install PyMySQL python-dotenv
```

## Database Configuration

### Railway Production Database
- **Host**: `shortline.proxy.rlwy.net`
- **Port**: `43260`
- **User**: `root`
- **Database**: `railway`

### Local Development Database
- **Host**: `localhost`
- **Port**: `3306`
- **User**: `GOMS`
- **Password**: `PGOMS`
- **Database**: `garment_db`

## What the Scripts Do

1. **🔍 Check Requirements**: Verify that MySQL client tools are available
2. **🔗 Test Connections**: Test connectivity to both Railway and local databases
3. **💾 Create Backup**: Create a timestamped backup of your current local database
4. **📤 Export from Railway**: Export the complete database from Railway production
5. **🗑️ Clear Local Database**: Remove all existing data from local database
6. **📥 Import Data**: Import the Railway data into your local database
7. **🧹 Cleanup**: Remove temporary files

## Safety Features

- **Automatic Backup**: Your local database is automatically backed up before any changes
- **Confirmation Prompt**: Scripts ask for confirmation before proceeding
- **Connection Testing**: Verifies both databases are accessible before starting
- **Error Handling**: Provides clear error messages and rollback instructions

## Backup Files

Backup files are created with the format: `backup_garment_db_YYYYMMDD_HHMMSS.sql`

To restore from a backup:
```bash
mysql -h localhost -u GOMS -pPGOMS garment_db < backup_garment_db_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting

### Connection Issues
- Ensure your local MySQL server is running
- Verify the `garment_db` database exists locally
- Check that you have internet connectivity for Railway access

### Permission Issues
- Make sure the local MySQL user `GOMS` has full privileges on the `garment_db` database
- Verify that the Railway database credentials are correct

### Import Failures
- Check that your local database has enough disk space
- Ensure no other processes are using the database
- Review the error messages for specific issues

## Security Note

The Railway database credentials are embedded in these scripts for convenience. In a production environment, consider:
- Using environment variables for sensitive data
- Implementing proper access controls
- Regular credential rotation

## Support

If you encounter issues:
1. Check the error messages carefully
2. Verify all prerequisites are met
3. Test database connections manually
4. Review the backup files if import fails
