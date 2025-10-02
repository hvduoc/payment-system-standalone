"""
Authentication và User Management Service
Xử lý đăng nhập, đăng ký, quản lý người dùng
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database_production import User, get_db
import secrets

# Secret key cho JWT
SECRET_KEY = "payment-secret-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 giờ

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash mật khẩu"""
    return pwd_context.hash(password)

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

def authenticate_user(db: Session, username: str, password: str):
    """Xác thực người dùng"""
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

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

def create_user(db: Session, username: str, password: str, full_name: str, role: str, phone: str = None, email: str = None):
    """Tạo người dùng mới"""
    # Kiểm tra username đã tồn tại chưa
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError(f"Username '{username}' đã tồn tại")
    
    # Tạo user mới
    hashed_password = get_password_hash(password)
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

def get_users_by_role(db: Session, role: str):
    """Lấy người dùng theo vai trò"""
    return db.query(User).filter(User.role == role, User.is_active == True).all()

def update_user(db: Session, user_id: int, **kwargs):
    """Cập nhật thông tin người dùng"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Không tìm thấy người dùng")
    
    for key, value in kwargs.items():
        if hasattr(user, key):
            if key == "password" and value:
                setattr(user, "password_hash", get_password_hash(value))
            else:
                setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user

def deactivate_user(db: Session, user_id: int):
    """Vô hiệu hóa người dùng"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Không tìm thấy người dùng")
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return user

# Các vai trò hệ thống
ROLES = {
    "assistant": "Trợ lý",
    "manager": "Quản lý", 
    "owner": "Chủ sở hữu"
}

def get_role_display_name(role: str) -> str:
    """Lấy tên hiển thị của vai trò"""
    return ROLES.get(role, role)
