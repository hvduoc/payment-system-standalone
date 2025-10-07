"""
Database configuration hỗ trợ cả SQLite (dev) và PostgreSQL (production)
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Timezone support - fallback cho Python < 3.9
try:
    from zoneinfo import ZoneInfo
    vietnam_tz = ZoneInfo('Asia/Ho_Chi_Minh')
except ImportError:
    # Fallback for Python < 3.9
    from datetime import timezone, timedelta
    vietnam_tz = timezone(timedelta(hours=7))  # UTC+7 for Vietnam

def get_vietnam_time():
    """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
    return datetime.now(vietnam_tz)

# Lấy DATABASE_URL từ environment (Railway sẽ cung cấp)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production: PostgreSQL từ Railway
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
    print("🚀 Kết nối PostgreSQL production")
else:
    # Development: SQLite local
    DATABASE_URL = "sqlite:///./payment_ledger.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print("💻 Sử dụng SQLite development")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Building(Base):
    """Bảng tòa nhà"""
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)  # Thêm field này
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None), onupdate=lambda: get_vietnam_time().replace(tzinfo=None))

class User(Base):
    """Bảng người dùng"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # assistant, manager, owner
    phone = Column(String(15), nullable=True)
    email = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    building_id = Column(Integer, nullable=True)  # Gán user cho tòa nhà cụ thể
    created_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None), onupdate=lambda: get_vietnam_time().replace(tzinfo=None))

class Payment(Base):
    """Bảng ghi nhận thu"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, nullable=True)  # Thuộc tòa nhà nào
    booking_id = Column(String(50), nullable=False)
    guest_name = Column(String(100), nullable=False)
    room_number = Column(String(20), nullable=True)  # Phòng số mấy
    amount_due = Column(Float, nullable=False)
    amount_collected = Column(Float, nullable=False)
    payment_method = Column(String(30), nullable=False)
    collected_by = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    receipt_image = Column(String(255), nullable=True)
    status = Column(String(20), default="completed")
    added_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None), onupdate=lambda: get_vietnam_time().replace(tzinfo=None))

class Handover(Base):
    """Bảng bàn giao tiền mặt"""
    __tablename__ = "handovers"
    
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, nullable=True)  # Thuộc tòa nhà nào
    from_person = Column(String(100), nullable=False)  # Người bàn giao
    to_person = Column(String(100), nullable=False)    # Người nhận
    amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    image_path = Column(String(255), nullable=True)
    status = Column(String(20), default="completed")
    handover_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: get_vietnam_time().replace(tzinfo=None), onupdate=lambda: get_vietnam_time().replace(tzinfo=None))

# Tạo tất cả các bảng
def create_tables():
    """Tạo tất cả các bảng trong database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables được tạo/cập nhật thành công")

# Dependency để lấy database session
def get_db():
    """Lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("✅ Hoàn thành thiết lập database!")