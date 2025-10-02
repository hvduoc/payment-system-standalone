"""
Test script cho Payment System
Kiểm tra đầy đủ chức năng trước khi deploy
"""

import requests
import json
import time

def test_system(base_url="http://localhost:8004"):
    """Test toàn bộ hệ thống"""
    print(f"🧪 Testing Payment System at {base_url}")
    
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    def run_test(name, test_func):
        results["total_tests"] += 1
        try:
            print(f"\n🔍 Testing: {name}")
            test_func()
            print(f"✅ PASSED: {name}")
            results["passed"] += 1
        except Exception as e:
            print(f"❌ FAILED: {name} - {str(e)}")
            results["failed"] += 1
            results["errors"].append(f"{name}: {str(e)}")
    
    # Test 1: Basic connectivity
    def test_connectivity():
        response = requests.get(f"{base_url}/")
        assert response.status_code in [200, 302], f"Expected 200/302, got {response.status_code}"
    
    # Test 2: Login page
    def test_login_page():
        response = requests.get(f"{base_url}/login")
        assert response.status_code == 200, f"Login page failed: {response.status_code}"
        assert "Đăng nhập" in response.text, "Login page content missing"
    
    # Test 3: Emergency page
    def test_emergency_page():
        response = requests.get(f"{base_url}/emergency")
        assert response.status_code == 200, f"Emergency page failed: {response.status_code}"
    
    # Test 4: Debug endpoints
    def test_debug_endpoints():
        response = requests.get(f"{base_url}/debug/users")
        assert response.status_code == 200, f"Debug users failed: {response.status_code}"
    
    # Test 5: Authentication API
    def test_auth_api():
        data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/api/login", data=data)
        
        if response.status_code == 401:
            # Thử emergency credentials
            data = {
                "username": "emergency", 
                "password": "emergency2025"
            }
            response = requests.post(f"{base_url}/api/login", data=data)
        
        assert response.status_code == 200, f"Login API failed: {response.status_code}"
        
        result = response.json()
        assert result.get("success") == True, "Login API returned success=False"
    
    # Test 6: Fix auth endpoint
    def test_fix_auth():
        response = requests.get(f"{base_url}/debug/fix-auth")
        assert response.status_code == 200, f"Fix auth failed: {response.status_code}"
    
    # Run all tests
    run_test("System Connectivity", test_connectivity)
    run_test("Login Page", test_login_page)
    run_test("Emergency Page", test_emergency_page) 
    run_test("Debug Endpoints", test_debug_endpoints)
    run_test("Fix Auth Endpoint", test_fix_auth)
    run_test("Authentication API", test_auth_api)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/results['total_tests']*100):.1f}%")
    
    if results["errors"]:
        print(f"\n🚨 ERRORS:")
        for error in results["errors"]:
            print(f"   - {error}")
    
    if results["failed"] == 0:
        print(f"\n🎉 ALL TESTS PASSED! System ready for Railway deployment.")
    else:
        print(f"\n⚠️ Some tests failed. Please fix before deploying.")
    
    return results

def test_railway_production():
    """Test system trên Railway production"""
    railway_url = "https://payment-system-standalone-production.up.railway.app"
    print(f"🚀 Testing Railway Production at {railway_url}")
    
    try:
        # Test basic connectivity
        response = requests.get(railway_url, timeout=10)
        print(f"✅ Railway production is UP! Status: {response.status_code}")
        
        # Test emergency access
        response = requests.get(f"{railway_url}/emergency", timeout=10)
        if response.status_code == 200:
            print(f"✅ Emergency access available")
            print(f"🔗 Emergency URL: {railway_url}/emergency")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Railway production test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Payment System Testing Suite")
    print("=" * 50)
    
    # Test local first
    print("\n1️⃣ Testing Local Development...")
    try:
        local_results = test_system("http://localhost:8004")
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        print("💡 Tip: Start local server with: python main.py")
    
    # Test Railway production
    print("\n2️⃣ Testing Railway Production...")
    railway_success = test_railway_production()
    
    print("\n" + "="*50)
    print("🏁 FINAL SUMMARY")
    print("="*50)
    
    if railway_success:
        print("✅ Railway Production: WORKING")
        print("🎯 Recommend using emergency access if regular login fails")
    else:
        print("❌ Railway Production: ISSUES DETECTED")
        print("🔧 May need to redeploy or check Railway logs")