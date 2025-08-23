# 🚂 Railway to Local Database Copy Guide

This guide shows you how to copy data from your Railway database to your local MySQL database.

## 📋 Prerequisites

### 1. MySQL Client Tools
You need MySQL client tools installed on your system:

**macOS:**
```bash
brew install mysql-client
```

**Ubuntu/Debian:**
```bash
sudo apt-get install mysql-client
```

**Windows:**
Download and install MySQL Workbench or MySQL Shell from the official MySQL website.

### 2. Railway Database URL
You'll need your Railway database connection URL. You can find this in your Railway dashboard:
- Go to your Railway project
- Click on your database service
- Copy the connection URL

## 🔄 Method 1: Using mysqldump (Recommended)

This method creates a complete database backup and restores it locally.

### Step 1: Set Environment Variable (Optional)
```bash
export RAILWAY_DATABASE_URL="mysql://username:password@host:port/database"
```

### Step 2: Run the Copy Script
```bash
cd backend
python3 copy_railway_data.py
```

### Step 3: Follow the Prompts
The script will:
1. Ask for your Railway database URL (if not set as environment variable)
2. Show you the configuration
3. Ask for confirmation
4. Dump the Railway database to a SQL file
5. Restore the data to your local database

## 🔄 Method 2: Using Python/SQLAlchemy

This method copies data table by table using Python.

### Step 1: Install Required Packages
```bash
pip install pandas sqlalchemy pymysql
```

### Step 2: Run the Python Copy Script
```bash
cd backend
python3 copy_railway_data_python.py
```

### Step 3: Follow the Prompts
The script will:
1. Connect to both databases
2. Show you all tables found in Railway
3. Copy each table's data to your local database
4. Provide a summary of successful/failed copies

## 🔄 Method 3: Manual mysqldump (Advanced)

If you prefer to do it manually:

### Step 1: Dump Railway Database
```bash
mysqldump --host=your-railway-host \
          --port=your-railway-port \
          --user=your-railway-username \
          --password=your-railway-password \
          --single-transaction \
          --routines \
          --triggers \
          your-railway-database > railway_backup.sql
```

### Step 2: Restore to Local Database
```bash
mysql --host=localhost \
      --user=GOMS \
      --password=PGOMS \
      garment_db < railway_backup.sql
```

## 🔄 Method 4: Using Railway CLI (Alternative)

If you have Railway CLI installed:

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login to Railway
```bash
railway login
```

### Step 3: Connect to Your Project
```bash
railway link
```

### Step 4: Get Database URL
```bash
railway variables
```

### Step 5: Use the URL with Method 1 or 2

## 🛠️ Troubleshooting

### Common Issues:

1. **MySQL tools not found**
   - Install MySQL client tools for your operating system
   - Make sure they're in your PATH

2. **Connection refused**
   - Check if your Railway database is accessible
   - Verify the connection URL is correct
   - Ensure your IP is whitelisted in Railway (if required)

3. **Permission denied**
   - Check your Railway database user permissions
   - Verify your local MySQL user has CREATE/DROP privileges

4. **Table structure conflicts**
   - The Python method handles this better than mysqldump
   - You may need to manually adjust table structures

### Error Messages:

- **"Access denied"**: Check username/password
- **"Host not found"**: Check hostname/port
- **"Database doesn't exist"**: Check database name
- **"Table doesn't exist"**: Check table names

## 📊 Verification

After copying, verify the data:

1. **Check table counts:**
```sql
SELECT COUNT(*) FROM your_table_name;
```

2. **Compare row counts between databases**
3. **Test your application with the local data**

## 🧹 Cleanup

After successful copy:
- Delete the backup SQL file if you don't need it
- Remove the environment variable if you set one

## 🔒 Security Notes

- Never commit database credentials to version control
- Use environment variables for sensitive data
- Delete backup files after successful restore
- Consider encrypting backup files for sensitive data

## 📞 Support

If you encounter issues:
1. Check the error messages carefully
2. Verify your database URLs
3. Ensure MySQL tools are properly installed
4. Check network connectivity to Railway
