"""
Production Database Initialization
Tạo demo users cho Railway PostgreSQL
"""

import os
import sys
from database_production import SessionLocal, User, create_tables
import hashlib

def init_production_users():
    """Khởi tạo demo users cho production"""
    print("🚀 Initializing production database...")
    
    # Tạo tables trước
    create_tables()
    print("✅ Database tables created/updated")
    
    db = SessionLocal()
    
    try:
        # Xóa tất cả users cũ nếu có (fresh start)
        existing_users = db.query(User).count()
        print(f"📊 Existing users in database: {existing_users}")
        
        if existing_users == 0:
            print("👤 Creating demo users...")
            
            # Demo users với SHA256 hash
            demo_users = [
                {
                    "username": "admin",
                    "password": "admin123", 
                    "full_name": "Admin System",
                    "role": "owner",
                    "phone": "0901234567",
                    "email": "admin@airbnb.com"
                },
                {
                    "username": "emergency",
                    "password": "emergency2025",
                    "full_name": "Emergency Access", 
                    "role": "owner",
                    "phone": "0000000000",
                    "email": "emergency@airbnb.com"
                },
                {
                    "username": "manager1",
                    "password": "manager123",
                    "full_name": "Nguyễn Văn Quản Lý",
                    "role": "manager", 
                    "phone": "0907654321",
                    "email": "manager@airbnb.com"
                },
                {
                    "username": "assistant1",
                    "password": "assistant123",
                    "full_name": "Trần Thị Trợ Lý",
                    "role": "assistant",
                    "phone": "0908765432", 
                    "email": "assistant@airbnb.com"
                }
            ]
            
            for user_data in demo_users:
                # SHA256 hash password
                password_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
                
                user = User(
                    username=user_data["username"],
                    password_hash=password_hash,
                    full_name=user_data["full_name"], 
                    role=user_data["role"],
                    phone=user_data["phone"],
                    email=user_data["email"],
                    is_active=True
                )
                
                db.add(user)
                print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
            
            db.commit()
            print("💾 All users committed to database")
            
        else:
            print("👥 Users already exist, skipping creation")
            
        # Verify users
        users = db.query(User).all()
        print(f"\n📋 Final user count: {len(users)}")
        for user in users:
            print(f"   - {user.username}: {user.role} ({user.full_name})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error initializing users: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_production_auth():
    """Test authentication với production users"""
    print("\n🧪 Testing authentication...")
    
    # Import auth function
    try:
        from auth_service_simple import authenticate_user
    except ImportError:
        from auth_service import authenticate_user
    
    db = SessionLocal()
    
    test_accounts = [
        ("admin", "admin123"),
        ("manager1", "manager123"),
        ("emergency", "emergency2025")
    ]
    
    for username, password in test_accounts:
        try:
            user = authenticate_user(db, username, password)
            if user:
                print(f"✅ {username}: Login SUCCESS")
            else:
                print(f"❌ {username}: Login FAILED")
        except Exception as e:
            print(f"❌ {username}: Error - {e}")
    
    db.close()

if __name__ == "__main__":
    print("🎯 Railway Production Database Initialization")
    print("=" * 50)
    
    # Check if running on Railway (has DATABASE_URL)
    if os.getenv("DATABASE_URL"):
        print("🚂 Detected Railway environment (PostgreSQL)")
    else:
        print("💻 Local environment (SQLite)")
    
    success = init_production_users()
    
    if success:
        test_production_auth()
        print("\n🎉 Production database ready!")
        print("\n👤 Login credentials:")
        print("   - Admin: admin / admin123")
        print("   - Manager: manager1 / manager123") 
        print("   - Emergency: emergency / emergency2025")
        print("   - Assistant: assistant1 / assistant123")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)