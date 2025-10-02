"""
Debug script để tạo user admin trực tiếp trên production
"""
import os
from database_production import create_tables, SessionLocal, User
from auth_service import get_password_hash

def create_admin_user():
    """Tạo user admin với password đơn giản"""
    print("🔧 Creating admin user for production...")
    
    # Tạo tables
    create_tables()
    print("✅ Tables created/updated")
    
    db = SessionLocal()
    
    try:
        # Xóa user admin cũ nếu có
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            db.delete(existing_admin)
            print("🗑️ Deleted existing admin user")
        
        # Tạo user admin mới với password hash đơn giản
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Administrator",
            role="owner",
            phone="0901234567", 
            email="admin@payment.com",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Role: owner")
        
        # Verify user exists
        verify_user = db.query(User).filter(User.username == "admin").first()
        if verify_user:
            print(f"✅ Verification: User {verify_user.username} exists with role {verify_user.role}")
        else:
            print("❌ Verification failed: User not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()