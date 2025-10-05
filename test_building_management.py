"""
Script test tính năng quản lý tòa nhà
"""

import requests
import json

BASE_URL = "http://localhost:8005"

def test_building_management():
    """Test CRUD operations for buildings"""
    
    # 1. Login first
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    session = requests.Session()
    
    print("1. Testing login...")
    login_response = session.post(f"{BASE_URL}/api/login", data=login_data)
    if login_response.status_code == 200:
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    # 2. Get current buildings
    print("\n2. Getting current buildings...")
    buildings_response = session.get(f"{BASE_URL}/api/buildings")
    if buildings_response.status_code == 200:
        buildings = buildings_response.json()["buildings"]
        print(f"✅ Found {len(buildings)} buildings")
        for building in buildings:
            print(f"   - {building['id']}: {building['name']}")
    else:
        print(f"❌ Failed to get buildings: {buildings_response.status_code}")
        return
    
    # 3. Test create building
    print("\n3. Testing create building...")
    new_building_data = {
        "name": "Test Building Automation",
        "address": "123 Test Street, Test City",
        "description": "Building created by automation test"
    }
    
    create_response = session.post(f"{BASE_URL}/api/buildings", data=new_building_data)
    if create_response.status_code == 200:
        result = create_response.json()
        new_building_id = result["building_id"]
        print(f"✅ Created building with ID: {new_building_id}")
    else:
        print(f"❌ Failed to create building: {create_response.status_code}")
        return
    
    # 4. Test update building
    print("\n4. Testing update building...")
    update_data = {
        "name": "Updated Test Building",
        "address": "456 Updated Street, Updated City", 
        "description": "Updated description by automation test"
    }
    
    update_response = session.put(f"{BASE_URL}/api/buildings/{new_building_id}", data=update_data)
    if update_response.status_code == 200:
        print("✅ Building updated successfully")
    else:
        print(f"❌ Failed to update building: {update_response.status_code}")
        print(update_response.text)
    
    # 5. Test delete building
    print("\n5. Testing delete building...")
    delete_response = session.delete(f"{BASE_URL}/api/buildings/{new_building_id}")
    if delete_response.status_code == 200:
        print("✅ Building deleted successfully")
    else:
        print(f"❌ Failed to delete building: {delete_response.status_code}")
        print(delete_response.text)
    
    # 6. Final buildings list
    print("\n6. Final buildings list...")
    final_response = session.get(f"{BASE_URL}/api/buildings")
    if final_response.status_code == 200:
        final_buildings = final_response.json()["buildings"]
        print(f"✅ Final count: {len(final_buildings)} buildings")
        for building in final_buildings:
            print(f"   - {building['id']}: {building['name']}")
    
    print("\n🎉 Building management test completed!")

if __name__ == "__main__":
    test_building_management()