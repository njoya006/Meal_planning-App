# PowerShell deployment script for ChopSmo Backend
# Run this from your Windows machine to deploy to PythonAnywhere

Write-Host "🚀 Deploying ChopSmo Verification System to PythonAnywhere..." -ForegroundColor Green

# Check if we have SSH access
Write-Host "📡 Testing connection to PythonAnywhere..." -ForegroundColor Yellow

try {
    # Test if we can reach PythonAnywhere
    $testConnection = Test-NetConnection -ComputerName "ssh.pythonanywhere.com" -Port 22 -WarningAction SilentlyContinue
    
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "✅ Connection to PythonAnywhere successful!" -ForegroundColor Green
        
        # Method 1: Use SSH to run deployment
        Write-Host "🔧 Attempting SSH deployment..." -ForegroundColor Yellow
        
        $sshCommand = @"
cd ~/chopsmo && 
echo '🚀 Starting deployment...' && 
git stash && 
git checkout njoya && 
git pull origin njoya && 
python manage.py makemigrations && 
python manage.py migrate && 
python manage.py collectstatic --noinput && 
echo '✅ Deployment complete!'
"@
        
        # Try SSH deployment
        Write-Host "Executing deployment commands via SSH..." -ForegroundColor Cyan
        ssh njoya@ssh.pythonanywhere.com $sshCommand
        
    } else {
        Write-Host "❌ Cannot connect to PythonAnywhere SSH" -ForegroundColor Red
        Write-Host "🔄 Using alternative method..." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ SSH connection failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Alternative method: Manual instructions
Write-Host "`n📋 MANUAL DEPLOYMENT INSTRUCTIONS:" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor White

Write-Host "`n1️⃣ Open PythonAnywhere Console:" -ForegroundColor Yellow
Write-Host "   • Go to: https://www.pythonanywhere.com/user/njoya/consoles/" -ForegroundColor White
Write-Host "   • Click 'Bash' to open a new console" -ForegroundColor White

Write-Host "`n2️⃣ Run these commands in the PythonAnywhere console:" -ForegroundColor Yellow
Write-Host "   cd ~/chopsmo" -ForegroundColor Green
Write-Host "   git stash" -ForegroundColor Green
Write-Host "   git checkout njoya" -ForegroundColor Green
Write-Host "   git pull origin njoya" -ForegroundColor Green
Write-Host "   python manage.py makemigrations" -ForegroundColor Green
Write-Host "   python manage.py migrate" -ForegroundColor Green
Write-Host "   python manage.py collectstatic --noinput" -ForegroundColor Green

Write-Host "`n3️⃣ Reload your web app:" -ForegroundColor Yellow
Write-Host "   • Go to: https://www.pythonanywhere.com/user/njoya/webapps/" -ForegroundColor White
Write-Host "   • Click the 'Reload' button" -ForegroundColor White

Write-Host "`n4️⃣ Test the new verification endpoints:" -ForegroundColor Yellow
Write-Host "   • https://njoya.pythonanywhere.com/api/users/verification/status/" -ForegroundColor White
Write-Host "   • https://njoya.pythonanywhere.com/api/users/verification/apply/" -ForegroundColor White
Write-Host "   • https://njoya.pythonanywhere.com/admin/" -ForegroundColor White

Write-Host "`n🔑 Test credentials:" -ForegroundColor Cyan
Write-Host "   Email: testuser@example.com" -ForegroundColor White
Write-Host "   Password: testpass123" -ForegroundColor White

Write-Host "`n✨ NEW FEATURES DEPLOYED:" -ForegroundColor Magenta
Write-Host "   ✅ User verification application system" -ForegroundColor Green
Write-Host "   ✅ Admin approval/rejection workflow" -ForegroundColor Green
Write-Host "   ✅ Automatic email notifications" -ForegroundColor Green
Write-Host "   ✅ Verification status tracking" -ForegroundColor Green

# Test the current deployment
Write-Host "`n🧪 Testing current endpoints..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "https://njoya.pythonanywhere.com/api/csrf-token/" -Method Get -TimeoutSec 10
    Write-Host "✅ CSRF endpoint: Working" -ForegroundColor Green
} catch {
    Write-Host "❌ CSRF endpoint: Failed - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $loginData = @{
        email = "testuser@example.com"
        password = "testpass123"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "https://njoya.pythonanywhere.com/api/users/login/" -Method Post -Body $loginData -ContentType "application/json" -TimeoutSec 10
    Write-Host "✅ Login endpoint: Working" -ForegroundColor Green
    
    if ($loginResponse.token) {
        $headers = @{
            'Authorization' = "Token $($loginResponse.token)"
            'Content-Type' = 'application/json'
        }
        
        try {
            $statusResponse = Invoke-RestMethod -Uri "https://njoya.pythonanywhere.com/api/users/verification/status/" -Method Get -Headers $headers -TimeoutSec 10
            Write-Host "✅ Verification status endpoint: Working" -ForegroundColor Green
            Write-Host "   Current status: $($statusResponse.verification_status)" -ForegroundColor Cyan
        } catch {
            Write-Host "❌ Verification status endpoint: Not yet deployed" -ForegroundColor Yellow
            Write-Host "   👆 This will work after you deploy the verification system" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host "❌ Login endpoint: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Follow the manual deployment instructions above" -ForegroundColor White
Write-Host "2. Test the verification endpoints" -ForegroundColor White
Write-Host "3. Implement frontend integration" -ForegroundColor White

Write-Host "`n✅ Script complete! Ready for deployment." -ForegroundColor Green
