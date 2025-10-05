"""
Simple Authentication Service - Compatible với Railway
Sử dụng SHA256 thay vì bcrypt để tránh compatibility issues
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database_production import User, get_db
import hashlib
import os

# Secret key cho JWT - lấy từ environment hoặc default
SECRET_KEY = os.getenv("SECRET_KEY", "payment-secret-2025-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 giờ

def verify_password_simple(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu với SHA256"""
    try:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    except:
        return False

def get_password_hash_simple(password: str) -> str:
    """Hash mật khẩu với SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Tạo JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user_simple(db: Session, username: str, password: str):
    """Xác thực người dùng với SHA256"""
    try:
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user:
            print(f"❌ User not found: {username}")
            return False
        
        if not verify_password_simple(password, user.password_hash):
            print(f"❌ Password verification failed for: {username}")
            return False
        
        print(f"✅ Authentication successful for: {username}")
        return user
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

# Alias for compatibility
def authenticate_user(db: Session, username: str, password: str):
    """Alias cho authenticate_user_simple để compatibility"""
    return authenticate_user_simple(db, username, password)

def get_current_user_from_token(token: str, db: Session):
    """Lấy thông tin user từ JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    return user

def create_user_simple(db: Session, username: str, password: str, full_name: str, role: str, phone: str = None, email: str = None):
    """Tạo người dùng mới với SHA256"""
    # Kiểm tra username đã tồn tại chưa
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError(f"Username '{username}' đã tồn tại")
    
    # Tạo user mới
    hashed_password = get_password_hash_simple(password)
    new_user = User(
        username=username,
        password_hash=hashed_password,
        full_name=full_name,
        role=role,
        phone=phone,
        email=email,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def get_all_users(db: Session):
    """Lấy tất cả người dùng"""
    return db.query(User).filter(User.is_active == True).all()

# Các vai trò hệ thống
ROLES = {
    "assistant": "Trợ lý",
    "manager": "Quản lý", 
    "owner": "Chủ sở hữu"
}

def get_role_display_name(role: str) -> str:
    """Lấy tên hiển thị của vai trò"""
    return ROLES.get(role, role)

# Backward compatibility functions
verify_password = verify_password_simple
get_password_hash = get_password_hash_simple
authenticate_user = authenticate_user_simple
create_user = create_user_simple