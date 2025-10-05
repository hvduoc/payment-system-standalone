#!/bin/bash

# Deploy Payment System to Railway
echo "🚀 Preparing Payment System for Railway deployment..."

# 1. Git setup
echo "📁 Setting up Git repository..."
git add .
git status

echo "📝 Creating deployment commit..."
read -p "Enter commit message (default: Deploy mobile-optimized payment system): " commit_msg
commit_msg=${commit_msg:-"Deploy mobile-optimized payment system"}

git commit -m "$commit_msg"

echo "🔄 Pushing to GitHub..."
git push origin main

echo "✅ Code pushed to GitHub successfully!"

echo "🚂 Railway Deployment Steps:"
echo "1. Go to railway.app and connect your GitHub repo"
echo "2. Select the 'payment-system-standalone' repository"
echo "3. Set environment variables in Railway dashboard:"
echo "   - DATABASE_URL: \${{PostgreSQL.DATABASE_URL}}"
echo "   - SECRET_KEY: (generate a secure key)"
echo "   - PORT: 8000"
echo ""
echo "4. Railway will automatically:"
echo "   - Install Python dependencies from requirements.txt"
echo "   - Create PostgreSQL database"
echo "   - Deploy using Dockerfile"
echo ""
echo "🌐 After deployment, your app will be available at:"
echo "   https://your-project-name.railway.app"
echo ""
echo "📱 Mobile features deployed:"
echo "   ✅ Responsive design for mobile/tablet"
echo "   ✅ Touch-friendly navigation"
echo "   ✅ Mobile-first dashboard"
echo "   ✅ PWA-ready (can install on phone)"
echo "   ✅ Optimized for Airbnb management on-the-go"
echo ""
echo "🔧 Post-deployment checklist:"
echo "   1. Test login on mobile device"
echo "   2. Create sample payments via mobile interface"
echo "   3. Test building management features"
echo "   4. Verify responsive design on different screen sizes"
echo ""
echo "🎉 Deployment preparation complete!"
echo "Visit railway.app to complete the deployment process."