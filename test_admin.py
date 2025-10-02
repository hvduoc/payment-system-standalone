"""
Quick fix: Tạo admin user trực tiếp
"""
import requests

def create_admin_via_endpoint():
    """Tạo admin user qua endpoint production"""
    url = "https://payment-system-standalone-production.up.railway.app/debug/create-admin"
    
    try:
        response = requests.post(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def check_users():
    """Kiểm tra users hiện có"""
    url = "https://payment-system-standalone-production.up.railway.app/debug/users"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking current users...")
    check_users()
    
    print("\n🔧 Creating admin user...")
    create_admin_via_endpoint()
    
    print("\n✅ Checking users after creation...")
    check_users()