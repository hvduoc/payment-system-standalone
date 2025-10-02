"""
Tạo demo users cho hệ thống Payment Ledger
"""

from database import create_tables, SessionLocal, User
from auth_service import get_password_hash

def create_demo_users():
    """Tạo các demo users"""
    create_tables()
    
    db = SessionLocal()
    
    # Kiểm tra users đã tồn tại chưa
    existing_users = db.query(User).count()
    if existing_users > 0:
        print(f"✅ Đã có {existing_users} users trong database")
        return
    
    demo_users = [
        {
            "username": "admin",
            "password": "admin123",
            "full_name": "Quản trị viên",
            "role": "owner",
            "phone": "0901234567",
            "email": "admin@airbnb.com"
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
            "phone": "0909876543",
            "email": "assistant@airbnb.com"
        },
        {
            "username": "accountant",
            "password": "account123",
            "full_name": "Lê Thị Kế Toán", 
            "role": "manager",
            "phone": "0903456789",
            "email": "accountant@airbnb.com"
        }
    ]
    
    for user_data in demo_users:
        user = User(
            username=user_data["username"],
            password_hash=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            phone=user_data["phone"],
            email=user_data["email"],
            is_active=True
        )
        db.add(user)
    
    db.commit()
    db.close()
    
    print("✅ Đã tạo demo users thành công:")
    for user_data in demo_users:
        print(f"   👤 {user_data['username']} / {user_data['password']} ({user_data['role']})")

if __name__ == "__main__":
    create_demo_users()