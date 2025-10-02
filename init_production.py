"""
Script khởi tạo cho Railway Production
Tạo tables và demo users cho lần đầu deploy
"""

import os
from database_production import create_tables, SessionLocal, User
from auth_service import get_password_hash

def init_production_database():
    """Khởi tạo database production lần đầu"""
    print("🚀 Bắt đầu khởi tạo database production...")
    
    # Tạo tables
    create_tables()
    
    # Kiểm tra và tạo admin user
    db = SessionLocal()
    
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("👤 Tạo admin user...")
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                full_name="Quản trị viên",
                role="owner",
                phone="0901234567",
                email="admin@payment-system.com",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Đã tạo admin user: admin/admin123")
        else:
            print("✅ Admin user đã tồn tại")
            
        # Tạo manager demo
        manager_user = db.query(User).filter(User.username == "manager1").first()
        if not manager_user:
            print("👤 Tạo manager user...")
            manager_user = User(
                username="manager1",
                password_hash=get_password_hash("manager123"),
                full_name="Nguyễn Văn Quản Lý",
                role="manager", 
                phone="0907654321",
                email="manager@payment-system.com",
                is_active=True
            )
            db.add(manager_user)
            db.commit()
            print("✅ Đã tạo manager user: manager1/manager123")
        else:
            print("✅ Manager user đã tồn tại")
            
        print("🎉 Hoàn thành khởi tạo database production!")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_production_database()