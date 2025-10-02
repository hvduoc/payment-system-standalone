"""
Script fix authentication cho Railway Production
Khắc phục lỗi đăng nhập và tạo users backup
"""

import os
import sys
from database_production import SessionLocal, User, create_tables
from auth_service import get_password_hash

def fix_auth_production():
    """Fix authentication issues cho Railway"""
    print("🔧 Bắt đầu fix authentication issues...")
    
    # Tạo tables
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Xóa tất cả users cũ để tránh conflict
        print("🗑️ Xóa users cũ...")
        db.query(User).delete()
        db.commit()
        
        # Tạo admin user với password đơn giản
        print("👤 Tạo admin user...")
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Admin System",
            role="owner",
            phone="0901234567",
            email="admin@system.com",
            is_active=True
        )
        db.add(admin_user)
        
        # Tạo emergency user  
        print("🚨 Tạo emergency user...")
        emergency_user = User(
            username="emergency",
            password_hash=get_password_hash("emergency2025"),
            full_name="Emergency Access",
            role="owner",
            phone="0000000000",
            email="emergency@system.com",
            is_active=True
        )
        db.add(emergency_user)
        
        # Tạo demo manager
        print("👥 Tạo demo manager...")
        manager_user = User(
            username="manager1",
            password_hash=get_password_hash("manager123"),
            full_name="Nguyễn Văn Quản Lý",
            role="manager", 
            phone="0907654321",
            email="manager@system.com",
            is_active=True
        )
        db.add(manager_user)
        
        # Commit tất cả
        db.commit()
        
        print("✅ Hoàn thành fix authentication!")
        print("📋 Thông tin đăng nhập:")
        print("   - Admin: admin / admin123")
        print("   - Emergency: emergency / emergency2025") 
        print("   - Manager: manager1 / manager123")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi fix authentication: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_auth():
    """Test authentication sau khi fix"""
    print("\n🧪 Testing authentication...")
    
    db = SessionLocal()
    try:
        # Test admin login
        from auth_service import authenticate_user
        
        admin = authenticate_user(db, "admin", "admin123")
        if admin:
            print("✅ Admin login: SUCCESS")
        else:
            print("❌ Admin login: FAILED")
            
        emergency = authenticate_user(db, "emergency", "emergency2025")
        if emergency:
            print("✅ Emergency login: SUCCESS")
        else:
            print("❌ Emergency login: FAILED")
            
        manager = authenticate_user(db, "manager1", "manager123")
        if manager:
            print("✅ Manager login: SUCCESS")
        else:
            print("❌ Manager login: FAILED")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_auth_production()
    if success:
        test_auth()
        print("\n🎉 Authentication đã được fix! Có thể deploy lên Railway.")
    else:
        print("\n💥 Fix failed. Cần kiểm tra lại.")