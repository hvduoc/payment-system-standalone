# Deploy Payment System to Railway - PowerShell Script

Write-Host "🚀 Preparing Payment System for Railway deployment..." -ForegroundColor Green

# Check if Git is initialized
if (!(Test-Path ".git")) {
    Write-Host "📁 Initializing Git repository..." -ForegroundColor Yellow
    git init
    git remote add origin https://github.com/yourusername/payment-system-standalone.git
    Write-Host "⚠️  Please update the GitHub repository URL above" -ForegroundColor Red
}

# 1. Git setup
Write-Host "📁 Adding files to Git..." -ForegroundColor Blue
git add .
git status

Write-Host ""
Write-Host "📝 Creating deployment commit..." -ForegroundColor Blue
$commitMsg = Read-Host "Enter commit message (default: Deploy mobile-optimized payment system)"
if ([string]::IsNullOrEmpty($commitMsg)) {
    $commitMsg = "Deploy mobile-optimized payment system"
}

git commit -m "$commitMsg"

Write-Host ""
Write-Host "🔄 Pushing to GitHub..." -ForegroundColor Blue
git push origin main

Write-Host ""
Write-Host "✅ Code pushed to GitHub successfully!" -ForegroundColor Green

Write-Host ""
Write-Host "🚂 Railway Deployment Instructions:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to https://railway.app and login" -ForegroundColor White
Write-Host "2. Click 'New Project' → 'Deploy from GitHub repo'" -ForegroundColor White
Write-Host "3. Select 'payment-system-standalone' repository" -ForegroundColor White
Write-Host "4. Railway will automatically detect Dockerfile" -ForegroundColor White
Write-Host ""
Write-Host "5. Add PostgreSQL database:" -ForegroundColor Yellow
Write-Host "   - Click '+ New' → 'Database' → 'Add PostgreSQL'" -ForegroundColor White
Write-Host ""
Write-Host "6. Set Environment Variables in Railway dashboard:" -ForegroundColor Yellow
Write-Host "   Variables → Add Variable:" -ForegroundColor White
Write-Host "   • SECRET_KEY: Generate a secure random key" -ForegroundColor White
Write-Host "   • PORT: 8000" -ForegroundColor White
Write-Host "   • DATABASE_URL: Will be auto-set by PostgreSQL service" -ForegroundColor White
Write-Host ""
Write-Host "🌐 After deployment, your app will be available at:" -ForegroundColor Green
Write-Host "   https://your-project-name.railway.app" -ForegroundColor White
Write-Host ""
Write-Host "📱 Mobile Features Deployed:" -ForegroundColor Magenta
Write-Host "   ✅ Responsive design for mobile/tablet" -ForegroundColor Green
Write-Host "   ✅ Touch-friendly navigation with hamburger menu" -ForegroundColor Green
Write-Host "   ✅ Mobile-first dashboard" -ForegroundColor Green
Write-Host "   ✅ PWA-ready (can install on phone like an app)" -ForegroundColor Green
Write-Host "   ✅ Optimized for Airbnb management on-the-go" -ForegroundColor Green
Write-Host "   ✅ Multi-building support with role-based access" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Post-deployment Testing Checklist:" -ForegroundColor Cyan
Write-Host "   1. Test login on mobile device" -ForegroundColor White
Write-Host "   2. Create sample buildings and payments" -ForegroundColor White
Write-Host "   3. Test responsive design on different screen sizes" -ForegroundColor White
Write-Host "   4. Try PWA installation (Add to Home Screen)" -ForegroundColor White
Write-Host "   5. Test building management features" -ForegroundColor White
Write-Host "   6. Verify touch-friendly navigation" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Deployment preparation complete!" -ForegroundColor Green
Write-Host "Visit https://railway.app to complete the deployment process." -ForegroundColor Yellow

# Generate a sample SECRET_KEY
Write-Host ""
Write-Host "🔑 Sample SECRET_KEY for Railway:" -ForegroundColor Yellow
$secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host $secretKey -ForegroundColor Cyan
Write-Host "Copy this key and paste it as SECRET_KEY in Railway environment variables" -ForegroundColor White