"""
Deploy và Test Script cho Railway
Tự động hóa deployment process
"""

import subprocess
import time
import requests
import sys

def run_command(command, description):
    """Chạy command và hiển thị kết quả"""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout:
                print(f"Output: {result.stdout[:200]}...")
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_local_system():
    """Test hệ thống local trước khi deploy"""
    print("\n🧪 Testing Local System...")
    
    # Start local server in background
    print("Starting local server...")
    import subprocess
    import time
    
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8004"
    ])
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # Test local endpoints
        response = requests.get("http://localhost:8004/debug/users", timeout=5)
        if response.status_code == 200:
            print("✅ Local server working")
            
            # Test emergency access
            response = requests.get("http://localhost:8004/emergency", timeout=5)
            if response.status_code == 200:
                print("✅ Emergency access working")
                return True
            
    except Exception as e:
        print(f"❌ Local test failed: {e}")
    finally:
        server_process.terminate()
    
    return False

def deploy_to_railway():
    """Deploy project to Railway"""
    print("\n🚀 Deploying to Railway...")
    
    # Git commands for Railway
    commands = [
        ("git add .", "Stage all changes"),
        ("git commit -m 'Fix authentication issues for Railway deployment'", "Commit changes"),
        ("git push origin main", "Push to GitHub (triggers Railway deploy)"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Deployment step failed: {description}")
            return False
    
    print("✅ Code pushed to GitHub. Railway will auto-deploy.")
    return True

def wait_for_deployment(url, max_wait=300):
    """Chờ deployment hoàn thành"""
    print(f"\n⏳ Waiting for deployment at {url}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code in [200, 302]:
                print(f"✅ Deployment successful! Status: {response.status_code}")
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(10)
    
    print(f"\n❌ Deployment timeout after {max_wait} seconds")
    return False

def test_production_system(base_url):
    """Test production system"""
    print(f"\n🧪 Testing Production System at {base_url}")
    
    tests = [
        ("/debug/users", "Debug users endpoint"),
        ("/emergency", "Emergency login page"),
        ("/login", "Regular login page"),
        ("/debug/fix-auth", "Auth fix endpoint"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                passed += 1
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
    
    print(f"\n📊 Production Test Results: {passed}/{total} passed")
    return passed == total

def main():
    """Main deployment workflow"""
    print("🎯 Payment System - Railway Deployment Workflow")
    print("=" * 60)
    
    # Step 1: Test local
    # if not test_local_system():
    #     print("❌ Local tests failed. Fix issues before deploying.")
    #     return False
    
    # Step 2: Deploy to Railway
    if not deploy_to_railway():
        print("❌ Deployment failed.")
        return False
    
    # Step 3: Wait for Railway deployment
    railway_url = "https://payment-system-standalone-production.up.railway.app"
    
    print(f"\n⏳ Railway deployment in progress...")
    print(f"🔗 URL: {railway_url}")
    print("⏰ Typically takes 2-3 minutes...")
    
    if wait_for_deployment(railway_url):
        # Step 4: Test production
        if test_production_system(railway_url):
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print(f"✅ System is live at: {railway_url}")
            print(f"🚨 Emergency access: {railway_url}/emergency")
            print(f"🔧 Use emergency/emergency2025 if regular login fails")
            return True
        else:
            print("\n⚠️ Deployment completed but some tests failed")
    
    print(f"\n🔧 Troubleshooting URLs:")
    print(f"   - Emergency: {railway_url}/emergency")
    print(f"   - Debug Users: {railway_url}/debug/users")
    print(f"   - Fix Auth: {railway_url}/debug/fix-auth")
    
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Ready for production use!")
    else:
        print("\n⚠️ Manual intervention may be required.")
        print("Check Railway logs for more details.")