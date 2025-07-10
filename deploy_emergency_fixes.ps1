# PowerShell script to deploy CORS and 500 error fixes to PythonAnywhere
# This script helps you upload and execute the fix_500_errors.py script on PythonAnywhere

Write-Host "🚀 ChopSmo Emergency Deployment Script" -ForegroundColor Green
Write-Host "This script will deploy fixes for the CORS and 500 errors" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor White

# Step 1: Check if you have the fix script
if (Test-Path -Path "fix_500_errors.py") {
    Write-Host "✅ Found fix_500_errors.py script" -ForegroundColor Green
} else {
    Write-Host "❌ Could not find fix_500_errors.py script in the current directory" -ForegroundColor Red
    Write-Host "Please run this script from the project root where fix_500_errors.py is located." -ForegroundColor Yellow
    exit
}

Write-Host "`n📋 DEPLOYMENT OPTIONS:" -ForegroundColor Cyan
Write-Host "1. Automatic deployment using SSH (recommended)" -ForegroundColor White
Write-Host "2. Manual step-by-step instructions" -ForegroundColor White

$option = Read-Host "Enter your choice (1 or 2)"

if ($option -eq "1") {
    Write-Host "`n🔄 Attempting automatic deployment..." -ForegroundColor Cyan
    
    # Check SSH command availability
    try {
        $null = Get-Command ssh -ErrorAction Stop
        Write-Host "✅ SSH command is available" -ForegroundColor Green
    } catch {
        Write-Host "❌ SSH command not found. Please install OpenSSH or use option 2." -ForegroundColor Red
        $option = "2"  # Fall back to manual instructions
    }
    
    if ($option -eq "1") {
        $username = Read-Host "Enter your PythonAnywhere username"
        Write-Host "Connecting to PythonAnywhere..." -ForegroundColor Yellow
        
        # First, upload the fix script
        Write-Host "Uploading fix_500_errors.py..." -ForegroundColor Yellow
        $uploadCommand = "scp fix_500_errors.py $username@ssh.pythonanywhere.com:~/"
        
        try {
            Invoke-Expression $uploadCommand
            Write-Host "✅ Successfully uploaded fix_500_errors.py" -ForegroundColor Green
            
            # Now run the fix script
            Write-Host "Running fix script on PythonAnywhere..." -ForegroundColor Yellow
            $sshCommand = "ssh $username@ssh.pythonanywhere.com 'cd ~ && python fix_500_errors.py'"
            Invoke-Expression $sshCommand
            
            # Upload the improved custom middleware
            Write-Host "Uploading custom_cors_middleware.py..." -ForegroundColor Yellow
            $uploadMiddlewareCommand = "scp meal_project/custom_cors_middleware.py $username@ssh.pythonanywhere.com:~/ChopSmo/meal_project/"
            Invoke-Expression $uploadMiddlewareCommand
            
            # Prompt to reload the web app
            Write-Host "`n✅ Fixes have been applied!" -ForegroundColor Green
            Write-Host "⚠️ You need to reload your web app on PythonAnywhere for changes to take effect:" -ForegroundColor Yellow
            Write-Host "1. Go to: https://www.pythonanywhere.com/user/$username/webapps/" -ForegroundColor White
            Write-Host "2. Click the green 'Reload' button for your web app" -ForegroundColor White
        } catch {
            Write-Host "❌ Error during automatic deployment: $_" -ForegroundColor Red
            Write-Host "Falling back to manual instructions..." -ForegroundColor Yellow
            $option = "2"  # Fall back to manual instructions
        }
    }
}

if ($option -eq "2") {
    Write-Host "`n📝 MANUAL DEPLOYMENT INSTRUCTIONS:" -ForegroundColor Cyan
    Write-Host "Follow these steps to deploy the fixes:" -ForegroundColor White
    
    Write-Host "`n1️⃣ Upload the fix scripts to PythonAnywhere:" -ForegroundColor Yellow
    Write-Host "   • Go to: https://www.pythonanywhere.com/user/YOUR_USERNAME/files/home/YOUR_USERNAME/" -ForegroundColor White
    Write-Host "   • Click 'Upload a file' and select fix_500_errors.py" -ForegroundColor White
    
    Write-Host "`n2️⃣ Open a PythonAnywhere Bash console:" -ForegroundColor Yellow
    Write-Host "   • Go to: https://www.pythonanywhere.com/user/YOUR_USERNAME/consoles/" -ForegroundColor White
    Write-Host "   • Click 'Bash' to open a new console" -ForegroundColor White
    
    Write-Host "`n3️⃣ Run the fix script:" -ForegroundColor Yellow
    Write-Host "   cd ~" -ForegroundColor Green
    Write-Host "   python fix_500_errors.py" -ForegroundColor Green
    
    Write-Host "`n4️⃣ Reload your web app:" -ForegroundColor Yellow
    Write-Host "   • Go to: https://www.pythonanywhere.com/user/YOUR_USERNAME/webapps/" -ForegroundColor White
    Write-Host "   • Click the green 'Reload' button for your web app" -ForegroundColor White
    
    Write-Host "`n5️⃣ Test if the 500 errors are fixed:" -ForegroundColor Yellow
    Write-Host "   • Try accessing your API from the frontend" -ForegroundColor White
    Write-Host "   • Check https://YOUR_USERNAME.pythonanywhere.com/api/csrf-token/ directly" -ForegroundColor White
}

Write-Host "`n🔍 AFTER DEPLOYMENT:" -ForegroundColor Cyan
Write-Host "To verify the fixes are working, check these URLs:" -ForegroundColor White
Write-Host "1. https://YOUR_USERNAME.pythonanywhere.com/api/csrf-token/" -ForegroundColor White
Write-Host "2. https://YOUR_USERNAME.pythonanywhere.com/api/users/login/ (using OPTIONS request)" -ForegroundColor White
Write-Host "3. https://YOUR_USERNAME.pythonanywhere.com/api/recipes/" -ForegroundColor White

Write-Host "`n⚠️ IMPORTANT SECURITY NOTE:" -ForegroundColor Red
Write-Host "These fixes temporarily enable DEBUG mode and CORS_ALLOW_ALL_ORIGINS." -ForegroundColor Yellow
Write-Host "Once everything is working properly, you should:" -ForegroundColor Yellow
Write-Host "1. Set DEBUG = False in settings.py" -ForegroundColor White
Write-Host "2. Replace CORS_ALLOW_ALL_ORIGINS = True with specific allowed origins" -ForegroundColor White
Write-Host "3. Reload your web app again" -ForegroundColor White

Write-Host "`n✅ Script complete! Follow the instructions above to fix the 500 errors." -ForegroundColor Green
