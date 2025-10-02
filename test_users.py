"""
Test all users login và user management
"""

import requests
import json

def test_all_users_login(base_url="https://payment-system-standalone-production.up.railway.app"):
    """Test login cho tất cả users"""
    print("🧪 Testing all users login...")
    
    users_to_test = [
        {"username": "admin", "password": "admin123", "expected_role": "owner"},
        {"username": "emergency", "password": "emergency2025", "expected_role": "owner"},
        {"username": "manager1", "password": "manager123", "expected_role": "manager"},
    ]
    
    results = []
    
    for user_data in users_to_test:
        print(f"\n🔍 Testing {user_data['username']}...")
        
        try:
            # Test via API login
            response = requests.post(f"{base_url}/api/login", data={
                "username": user_data["username"],
                "password": user_data["password"]
            }, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    user_info = result.get("user", {})
                    print(f"✅ Login SUCCESS: {user_info.get('full_name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
                    results.append({
                        "username": user_data["username"],
                        "status": "SUCCESS",
                        "role": user_info.get("role"),
                        "full_name": user_info.get("full_name"),
                        "id": user_info.get("id")
                    })
                else:
                    print(f"❌ Login FAILED: {result}")
                    results.append({
                        "username": user_data["username"],
                        "status": "FAILED",
                        "error": "API returned success=false"
                    })
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:100]}")
                results.append({
                    "username": user_data["username"], 
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                "username": user_data["username"],
                "status": "ERROR", 
                "error": str(e)
            })
    
    return results

def test_user_management_endpoints(base_url="https://payment-system-standalone-production.up.railway.app"):
    """Test user management endpoints"""
    print("\n🔧 Testing user management endpoints...")
    
    # Đầu tiên login với admin để có token
    try:
        login_response = requests.post(f"{base_url}/api/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print("❌ Cannot login as admin for testing")
            return False
        
        # Get cookies từ login response
        cookies = login_response.cookies
        
        # Test get all users
        users_response = requests.get(f"{base_url}/api/users", cookies=cookies)
        if users_response.status_code == 200:
            users = users_response.json().get("users", [])
            print(f"✅ Get users: {len(users)} users found")
            for user in users:
                print(f"   - {user.get('username')} ({user.get('role')}) - {user.get('full_name')}")
        else:
            print(f"❌ Get users failed: {users_response.status_code}")
        
        # Test create user
        print("\n🆕 Testing create new user...")
        new_user_data = {
            "username": "testuser",
            "password": "test123",
            "full_name": "Test User",
            "role": "assistant",
            "phone": "0123456789",
            "email": "test@example.com"
        }
        
        create_response = requests.post(f"{base_url}/api/admin/users", 
                                      data=new_user_data, cookies=cookies)
        
        if create_response.status_code == 200:
            result = create_response.json()
            if result.get("success"):
                print(f"✅ User created: {result['user']['username']}")
                test_user_id = result['user']['id']
                
                # Test login với user mới
                test_login_response = requests.post(f"{base_url}/api/test-login", data={
                    "username": "testuser",
                    "password": "test123"
                })
                
                if test_login_response.status_code == 200:
                    login_result = test_login_response.json()
                    if login_result.get("success"):
                        print("✅ New user can login successfully")
                    else:
                        print(f"❌ New user login failed: {login_result.get('message')}")
                
                # Test delete user
                delete_response = requests.delete(f"{base_url}/api/admin/users/{test_user_id}", 
                                                cookies=cookies)
                if delete_response.status_code == 200:
                    print("✅ User deleted (deactivated) successfully")
                else:
                    print(f"❌ Delete user failed: {delete_response.status_code}")
            else:
                print(f"❌ Create user failed: {result}")
        else:
            print(f"❌ Create user request failed: {create_response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ User management test error: {e}")
        return False

def main():
    print("🚀 Payment System User Testing Suite")
    print("=" * 50)
    
    # Test 1: Login all existing users
    login_results = test_all_users_login()
    
    print(f"\n📊 LOGIN TEST SUMMARY:")
    for result in login_results:
        status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
        print(f"   {status_icon} {result['username']}: {result['status']}")
        if result["status"] == "SUCCESS":
            print(f"      └─ {result.get('full_name', 'Unknown')} ({result.get('role', 'Unknown')})")
    
    # Test 2: User management
    management_success = test_user_management_endpoints()
    
    print(f"\n🏁 FINAL SUMMARY:")
    successful_logins = sum(1 for r in login_results if r["status"] == "SUCCESS")
    total_users = len(login_results)
    
    print(f"✅ Successful logins: {successful_logins}/{total_users}")
    print(f"🔧 User management: {'WORKING' if management_success else 'FAILED'}")
    
    if successful_logins == total_users and management_success:
        print(f"\n🎉 ALL TESTS PASSED! User system is fully operational.")
    else:
        print(f"\n⚠️ Some issues detected. Check individual test results.")

if __name__ == "__main__":
    main()