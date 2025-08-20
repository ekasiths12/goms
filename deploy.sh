#!/bin/bash

# Garment Management System - Railway Deployment Script

echo "🚀 Starting Railway deployment..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the garment_web_app directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
fi

# Check if remote is set
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  Warning: No git remote set. Please add your GitHub repository:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
    echo "   git push -u origin main"
fi

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Go to Railway.app and create new project"
echo "3. Connect your GitHub repository"
echo "4. Add MySQL database service"
echo "5. Set environment variables"
echo "6. Deploy!"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"
