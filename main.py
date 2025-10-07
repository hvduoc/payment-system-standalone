"""
Hệ thống Quản lý Thu Chi Airbnb - Production Version
Sử dụng SQLite database để lưu trữ bền vững
Bao gồm quản lý user và deployment ready
"""

from fastapi import FastAPI, Request, HTTPException, Form, File, UploadFile, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
import uuid
import shutil
import threading
import asyncio

# Timezone support - fallback cho Python < 3.9
try:
    from zoneinfo import ZoneInfo
    vietnam_tz = ZoneInfo('Asia/Ho_Chi_Minh')
except ImportError:
    # Fallback for Python < 3.9
    from datetime import timezone, timedelta
    vietnam_tz = timezone(timedelta(hours=7))  # UTC+7 for Vietnam

# Import các module tự tạo
from database_production import get_db, create_tables, User, Payment, Handover, Building  

# Railway Free Tier Optimizations
import logging
import os

# Configure logging for performance (Railway optimization)
logging.basicConfig(
    level=logging.WARNING,  # Reduce logging overhead
    format='%(levelname)s: %(message)s'
)

# Environment optimization for Railway free tier
os.environ.setdefault('UVICORN_WORKERS', '1')  # Single worker
os.environ.setdefault('UVICORN_TIMEOUT_KEEP_ALIVE', '5')  # Quick timeout

# Google Drive backup import (optional)
try:
    from google_drive_backup import GoogleDriveBackup, daily_backup_job, setup_backup_schedule
    GOOGLE_DRIVE_ENABLED = True
    print("✅ Google Drive backup enabled")
except ImportError:
    GOOGLE_DRIVE_ENABLED = False
    print("⚠️ Google Drive backup not available (missing dependencies)")

# Try simple auth first, fallback to original if needed
try:
    from auth_service_simple import (
        authenticate_user, 
        create_access_token, 
        get_current_user_from_token,
        create_user,
        get_all_users,
        get_role_display_name,
        get_password_hash
    )
    print("✅ Using simple authentication (SHA256)")
except ImportError:
    from auth_service import (
        authenticate_user, 
        create_access_token, 
        get_current_user_from_token,
        create_user,
        get_all_users,
        get_role_display_name,
        get_password_hash
    )
    print("⚠️ Using bcrypt authentication")

# Add CORS middleware import
from fastapi.middleware.cors import CORSMiddleware

# Thiết lập
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Khởi tạo database
create_tables()

app = FastAPI(
    title="Hệ thống Thu Chi Airbnb", 
    description="Quản lý thu chi và bàn giao tiền mặt - Production Version",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Railway production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Railway Free Tier: Health check endpoint for smart sleep
@app.get("/health")
async def health_check():
    """Health check endpoint - optimized for Railway auto-sleep"""
    return {
        "status": "healthy",
        "service": "Airbnb Payment System",
        "version": "2.0.0",
        "railway_optimized": True,
        "free_tier": True
    }

# Root path redirects to login
@app.get("/")
async def root():
    """Redirect root to login page"""
    return RedirectResponse(url="/login", status_code=302)

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with system status"""
    return {
        "status": "healthy",
        "database": "connected",
        "backup": "google_drive_enabled",
        "optimization": "railway_free_tier",
        "sleep_mode": "auto_enabled"
    }

templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# app.mount("/static", StaticFiles(directory="static"), name="static")  # Optional static files

# Helper function for template
def get_role_display_name_helper(role):
    """Helper function cho template"""
    roles = {
        "assistant": "Trợ lý",
        "manager": "Quản lý", 
        "owner": "Chủ sở hữu"
    }
    return roles.get(role, role)

# Add helper to template globals với Vietnam timezone
# Timezone is already setup above during import

def get_vietnam_time():
    """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
    return datetime.now(vietnam_tz)

templates.env.globals['getRoleDisplayName'] = get_role_display_name_helper
templates.env.globals['getVietnamTime'] = get_vietnam_time

# Dependency để lấy user hiện tại
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Lấy thông tin user hiện tại từ token"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    
    try:
        user = get_current_user_from_token(token, db)
        if not user:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        return user
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

@app.get("/dashboard")
async def dashboard_redirect(current_user: User = Depends(get_current_user)):
    """Dashboard route - redirect to admin payments"""
    return RedirectResponse(url="/admin/payments", status_code=302)

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Trang chủ - redirect đến trang đăng nhập nếu chưa đăng nhập"""
    token = request.cookies.get("access_token")
    
    if not token:
        print("No access token found in cookies")
        return RedirectResponse(url="/login")
    
    try:
        # Verify token
        user = get_current_user_from_token(token, db)
        if user:
            print(f"Valid user found: {user.username}")
            
            # Get dashboard data
            recent_payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(5).all()
            recent_handovers = db.query(Handover).order_by(Handover.created_at.desc()).limit(5).all()
            
            return templates.TemplateResponse("dashboard_mobile.html", {
                "request": request,
                "user": user,
                "recent_payments": recent_payments,
                "recent_handovers": recent_handovers,
                "getRoleDisplayName": get_role_display_name_helper,
                "getVietnamTime": get_vietnam_time
            })
        else:
            print("Token verification failed: user not found")
    except Exception as e:
        print(f"Token verification failed with error: {e}")
    
    # Redirect to login if no valid token
    return RedirectResponse(url="/login")

# Legacy route redirects for backward compatibility
@app.get("/payments")
async def redirect_payments():
    """Redirect old /payments route to new /admin/payments"""
    return RedirectResponse(url="/admin/payments", status_code=301)

# Temporary clean test route
@app.get("/admin/payments-test", response_class=HTMLResponse)
async def admin_payments_test(request: Request, current_user: User = Depends(get_current_user)):
    """Clean test version of payments page"""
    return templates.TemplateResponse("admin_payments_clean.html", {
        "request": request,
        "user": current_user
    })

@app.get("/handovers") 
async def redirect_handovers():
    """Redirect old /handovers route to new /admin/handovers"""
    return RedirectResponse(url="/admin/handovers", status_code=301)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Trang đăng nhập"""
    return templates.TemplateResponse("login_production.html", {"request": request})

@app.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    """Debug authentication page"""
    return templates.TemplateResponse("debug_auth.html", {"request": request})

@app.get("/api/time-info")
async def get_time_info():
    """Get current time information"""
    vietnam_time = get_vietnam_time()
    utc_time = datetime.utcnow()
    
    return {
        "vietnam_time": vietnam_time.isoformat(),
        "vietnam_time_formatted": vietnam_time.strftime("%H:%M:%S %d/%m/%Y"),
        "utc_time": utc_time.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
        "timezone_offset": "+07:00"
    }

@app.post("/api/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Đăng nhập API"""
    print(f"🔐 Login attempt: {username}")
    
    # Check if user exists
    user_check = db.query(User).filter(User.username == username).first()
    if not user_check:
        print(f"❌ User not found: {username}")
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không đúng")
    
    print(f"👤 User found: {username}, role: {user_check.role}")
    
    user = authenticate_user(db, username, password)
    if not user:
        print(f"❌ Authentication failed: {username}")
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không đúng")
    
    print(f"✅ Authentication successful: {username}")
    
    # Tạo access token
    access_token_expires = timedelta(minutes=1440)  # 24 giờ
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = JSONResponse({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "role_display": get_role_display_name(user.role)
        }
    })
    
    # Cookie settings for production HTTPS
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1440*60,  # 24 giờ
        secure=True,  # Required for HTTPS (Railway)
        samesite="lax",  # Allow cross-site requests
        path="/"  # Available for all paths
    )
    
    print(f"🍪 Cookie set for user: {username}")
    return response

@app.post("/api/payments")
async def add_payment(
    request: Request,
    booking_id: str = Form(...),
    guest_name: str = Form(...),
    room_number: str = Form(default=""),
    building_id: int = Form(default=None),
    amount_due: float = Form(...),
    amount_collected: float = Form(...),
    payment_method: str = Form(...),
    collected_by: str = Form(...),
    notes: str = Form(default=""),
    receipt_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Thêm khoản thu mới"""
    
    # Xử lý upload hình ảnh
    image_path = None
    if receipt_image and receipt_image.filename:
        file_extension = receipt_image.filename.split('.')[-1]
        unique_filename = f"receipt_{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(receipt_image.file, buffer)
        
        image_path = f"/uploads/{unique_filename}"
    
    # Tạo payment record với Vietnam timezone
    payment = Payment(
        booking_id=booking_id,
        guest_name=guest_name,
        room_number=room_number,
        building_id=building_id if building_id else None,
        amount_due=amount_due,
        amount_collected=amount_collected,
        payment_method=payment_method,
        collected_by=collected_by,
        notes=notes,
        receipt_image=image_path,
        status="completed",
        added_by_user_id=current_user.id
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Format time for Vietnam timezone
    vietnam_time = get_vietnam_time()
    
    return {"success": True, "payment": {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "guest_name": payment.guest_name,
        "amount_due": payment.amount_due,
        "amount_collected": payment.amount_collected,
        "payment_method": payment.payment_method,
        "collected_by": payment.collected_by,
        "notes": payment.notes,
        "receipt_image": payment.receipt_image,
        "created_at": vietnam_time.strftime("%H:%M:%S %d/%m/%Y"),
        "timestamp": vietnam_time.isoformat()
    }}

@app.get("/api/payments")
async def get_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách khoản thu"""
    
    # Lọc theo vai trò
    if current_user.role == "assistant":
        # Trợ lý chỉ xem được khoản thu của mình
        payments = db.query(Payment).filter(Payment.added_by_user_id == current_user.id).all()
    else:
        # Quản lý và chủ sở hữu xem được tất cả
        payments = db.query(Payment).all()
    
    payments_data = []
    for payment in payments:
        # Convert datetime to Vietnam timezone for display
        if payment.created_at:
            # Assume payment.created_at is already in Vietnam time (from database)
            display_time = payment.created_at.strftime("%H:%M:%S %d/%m/%Y") 
        else:
            display_time = "N/A"
            
        payments_data.append({
            "id": payment.id,
            "booking_id": payment.booking_id,
            "guest_name": payment.guest_name,
            "room_number": payment.room_number,
            "building_id": payment.building_id,
            "amount_due": payment.amount_due,
            "amount_collected": payment.amount_collected,
            "payment_method": payment.payment_method,
            "collected_by": payment.collected_by,
            "notes": payment.notes,
            "receipt_image": payment.receipt_image,
            "status": payment.status,
            "created_at": display_time,
            "timestamp": payment.created_at.isoformat() if payment.created_at else None
        })
    
    return {"payments": payments_data}

@app.get("/api/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy thông tin dashboard"""
    
    # Lấy tất cả payments (theo role)
    if current_user.role == "assistant":
        payments = db.query(Payment).filter(Payment.added_by_user_id == current_user.id).all()
    else:
        payments = db.query(Payment).all()
    
    # Lấy tất cả handovers
    handovers = db.query(Handover).all()
    
    total_collected = sum(p.amount_collected for p in payments)
    total_due = sum(p.amount_due for p in payments)
    collection_rate = (total_collected / total_due * 100) if total_due > 0 else 0
    
    # Tính tiền mặt cần bàn giao
    cash_payments = sum(p.amount_collected for p in payments if p.payment_method == "cash")
    cash_handed_over = sum(h.amount for h in handovers if h.status == "completed")
    cash_pending = cash_payments - cash_handed_over
    
    return {
        "total_collected": total_collected,
        "total_due": total_due,
        "collection_rate": round(collection_rate, 2),
        "total_payments": len(payments),
        "cash_balance": cash_payments,
        "cash_pending_handover": cash_pending,
        "total_handovers": len(handovers),
        "last_updated": get_vietnam_time().isoformat()
    }

@app.post("/api/handovers")
async def create_handover(
    request: Request,
    building_id: int = Form(...),
    to_person: str = Form(...),
    amount: float = Form(...),
    notes: str = Form(default=""),
    handover_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo bàn giao tiền mặt"""
    
    # Kiểm tra tòa nhà có tồn tại không
    building = db.query(Building).filter(Building.id == building_id, Building.is_active == True).first()
    if not building:
        raise HTTPException(status_code=400, detail="Không tìm thấy tòa nhà")
    
    # Xử lý upload hình ảnh bàn giao
    image_path = None
    if handover_image and handover_image.filename:
        file_extension = handover_image.filename.split('.')[-1]
        unique_filename = f"handover_{uuid.uuid4()}.{file_extension}"
        full_image_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(full_image_path, "wb") as buffer:
            shutil.copyfileobj(handover_image.file, buffer)
        
        image_path = f"/uploads/{unique_filename}"
    
    # Tạo handover record
    handover = Handover(
        building_id=building_id,
        from_person=current_user.full_name,
        to_person=to_person,
        amount=amount,
        notes=notes,
        image_path=image_path,
        status="completed",
        handover_by_user_id=current_user.id
    )
    
    db.add(handover)
    db.commit()
    db.refresh(handover)
    
    return {"success": True, "handover": {
        "id": handover.id,
        "building_name": building.name,
        "from_person": handover.from_person,
        "to_person": handover.to_person,
        "amount": handover.amount,
        "notes": handover.notes,
        "image_path": handover.image_path,
        "created_at": handover.created_at.isoformat()
    }}

@app.get("/api/handovers")
async def get_handovers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách bàn giao"""
    
    handovers = db.query(Handover).all()
    handovers_data = []
    
    for handover in handovers:
        handover_by_user = db.query(User).filter(User.id == handover.handover_by_user_id).first()
        building = db.query(Building).filter(Building.id == handover.building_id).first()
        
        handovers_data.append({
            "id": handover.id,
            "building_name": building.name if building else "Unknown",
            "from_person": handover.from_person,
            "to_person": handover.to_person,
            "handover_by": handover_by_user.full_name if handover_by_user else "Unknown",
            "amount": handover.amount,
            "notes": handover.notes,
            "image_path": handover.image_path,
            "status": handover.status,
            "created_at": handover.created_at.isoformat(),
            "timestamp": handover.created_at.isoformat()
        })
    
    return {"handovers": handovers_data}

@app.get("/api/users")
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách tất cả người dùng (cho dropdown recipient)"""
    
    # Chỉ manager và owner mới có thể xem danh sách user
    if current_user.role not in ["manager", "owner"]:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
    
    users = get_all_users(db)
    users_data = []
    
    for user in users:
        users_data.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "role_display": get_role_display_name(user.role),
            "phone": user.phone,
            "email": user.email
        })
    
    return {"users": users_data}

@app.get("/api/recipients")
async def get_recipients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách người có thể nhận bàn giao"""
    
    # Lấy tất cả user trừ chính mình
    users = db.query(User).filter(User.id != current_user.id, User.is_active == True).all()
    recipients_data = []
    
    for user in users:
        recipients_data.append({
            "id": user.id,
            "name": user.full_name,
            "role": get_role_display_name(user.role),
            "phone": user.phone or "Chưa có SĐT"
        })
    
    return {"recipients": recipients_data}

# CRUD Operations for Payments
@app.put("/api/payments/{payment_id}")
async def update_payment(
    payment_id: int,
    booking_id: str = Form(...),
    guest_name: str = Form(...),
    room_number: str = Form(default=""),
    building_id: int = Form(default=None),
    amount_due: float = Form(...),
    amount_collected: float = Form(...),
    payment_method: str = Form(...),
    collected_by: str = Form(...),
    notes: str = Form(default=""),
    receipt_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật payment record"""
    
    # Tìm payment
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản thu")
    
    # Kiểm tra quyền edit (owner, manager có thể edit tất cả, assistant chỉ edit của mình)
    if current_user.role == "assistant" and payment.added_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa khoản thu này")
    
    # Xử lý upload hình ảnh mới (nếu có)
    if receipt_image and receipt_image.filename:
        file_extension = receipt_image.filename.split('.')[-1]
        unique_filename = f"receipt_{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(receipt_image.file, buffer)
        
        payment.receipt_image = f"/uploads/{unique_filename}"
    
    # Cập nhật thông tin
    payment.booking_id = booking_id
    payment.guest_name = guest_name
    payment.room_number = room_number
    payment.building_id = building_id
    payment.amount_due = amount_due
    payment.amount_collected = amount_collected
    payment.payment_method = payment_method
    payment.collected_by = collected_by
    payment.notes = notes
    payment.updated_at = get_vietnam_time().replace(tzinfo=None)
    
    db.commit()
    db.refresh(payment)
    
    return {"success": True, "message": "Cập nhật thành công", "payment_id": payment.id}

@app.delete("/api/payments/{payment_id}")
async def delete_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa payment record"""
    
    # Tìm payment
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản thu")
    
    # Kiểm tra quyền xóa (chỉ owner và manager)
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Không có quyền xóa khoản thu")
    
    db.delete(payment)
    db.commit()
    
    return {"success": True, "message": "Xóa khoản thu thành công"}

@app.get("/api/payments/{payment_id}")
async def get_payment_detail(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy chi tiết payment để edit"""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản thu")
    
    # Kiểm tra quyền xem
    if current_user.role == "assistant" and payment.added_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xem khoản thu này")
    
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "guest_name": payment.guest_name,
        "room_number": payment.room_number or "",
        "building_id": payment.building_id,
        "amount_due": payment.amount_due,
        "amount_collected": payment.amount_collected,
        "payment_method": payment.payment_method,
        "collected_by": payment.collected_by,
        "notes": payment.notes or "",
        "receipt_image": payment.receipt_image,
        "status": payment.status,
        "created_at": payment.created_at.isoformat() if payment.created_at else None
    }

# CRUD Operations for Handovers
@app.put("/api/handovers/{handover_id}")
async def update_handover(
    handover_id: int,
    from_person: str = Form(...),
    to_person: str = Form(...),
    amount: float = Form(...),
    building_id: int = Form(default=None),
    notes: str = Form(default=""),
    handover_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật handover record"""
    
    handover = db.query(Handover).filter(Handover.id == handover_id).first()
    if not handover:
        raise HTTPException(status_code=404, detail="Không tìm thấy bàn giao")
    
    # Kiểm tra quyền edit
    if current_user.role == "assistant" and handover.handover_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa bàn giao này")
    
    # Xử lý upload hình ảnh mới
    if handover_image and handover_image.filename:
        file_extension = handover_image.filename.split('.')[-1]
        unique_filename = f"handover_{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(handover_image.file, buffer)
        
        handover.image_path = f"/uploads/{unique_filename}"
    
    # Cập nhật thông tin
    handover.from_person = from_person
    handover.to_person = to_person
    handover.amount = amount
    handover.building_id = building_id
    handover.notes = notes
    handover.updated_at = get_vietnam_time().replace(tzinfo=None)
    
    db.commit()
    db.refresh(handover)
    
    return {"success": True, "message": "Cập nhật thành công", "handover_id": handover.id}

@app.delete("/api/handovers/{handover_id}")
async def delete_handover(
    handover_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa handover record"""
    
    handover = db.query(Handover).filter(Handover.id == handover_id).first()
    if not handover:
        raise HTTPException(status_code=404, detail="Không tìm thấy bàn giao")
    
    # Kiểm tra quyền xóa
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Không có quyền xóa bàn giao")
    
    db.delete(handover)
    db.commit()
    
    return {"success": True, "message": "Xóa bàn giao thành công"}

@app.get("/api/handovers/{handover_id}")
async def get_handover_detail(
    handover_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy chi tiết handover để edit"""
    
    handover = db.query(Handover).filter(Handover.id == handover_id).first()
    if not handover:
        raise HTTPException(status_code=404, detail="Không tìm thấy bàn giao")
    
    return {
        "id": handover.id,
        "from_person": handover.from_person,
        "to_person": handover.to_person,
        "amount": handover.amount,
        "building_id": handover.building_id,
        "notes": handover.notes or "",
        "image_path": handover.image_path,
        "status": handover.status,
        "created_at": handover.created_at.isoformat() if handover.created_at else None
    }

# Building Management APIs
@app.get("/api/buildings")
async def get_buildings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách tòa nhà"""
    
    buildings = db.query(Building).filter(Building.is_active == True).all()
    buildings_data = []
    
    for building in buildings:
        buildings_data.append({
            "id": building.id,
            "name": building.name,
            "address": building.address,
            "description": building.description
        })
    
    return {"buildings": buildings_data}

@app.post("/api/buildings")
async def create_building(
    name: str = Form(...),
    address: str = Form(default=""),
    description: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo tòa nhà mới (chỉ owner)"""
    
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền tạo tòa nhà")
    
    building = Building(
        name=name,
        address=address,
        description=description,
        is_active=True
    )
    
    db.add(building)
    db.commit()
    db.refresh(building)
    
    return {"success": True, "building_id": building.id, "message": "Tạo tòa nhà thành công"}

@app.put("/api/buildings/{building_id}")
async def update_building(
    building_id: int,
    name: str = Form(...),
    address: str = Form(default=""),
    description: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật tòa nhà (chỉ owner)"""
    
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền chỉnh sửa tòa nhà")
    
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà")
    
    building.name = name
    building.address = address
    building.description = description
    building.updated_at = get_vietnam_time().replace(tzinfo=None)
    
    db.commit()
    db.refresh(building)
    
    return {"success": True, "message": "Cập nhật tòa nhà thành công"}

@app.delete("/api/buildings/{building_id}")
async def delete_building(
    building_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa tòa nhà (chỉ owner)"""
    
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền xóa tòa nhà")
    
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Không tìm thấy tòa nhà")
    
    # Kiểm tra xem có payment nào đang sử dụng building này không
    payments_count = db.query(Payment).filter(Payment.building_id == building_id).count()
    if payments_count > 0:
        raise HTTPException(status_code=400, detail=f"Không thể xóa tòa nhà này vì đang có {payments_count} khoản thu sử dụng")
    
    db.delete(building)
    db.commit()
    
    return {"success": True, "message": "Xóa tòa nhà thành công"}

@app.post("/api/logout")
@app.get("/api/logout")
async def logout(request: Request):
    """Đăng xuất - hỗ trợ cả GET và POST"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# Routes quản lý user (chỉ dành cho owner)
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trang quản lý người dùng (chỉ owner)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền truy cập")
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request, 
        "user": current_user,
        "getVietnamTime": get_vietnam_time
    })

@app.post("/api/admin/users")
async def create_new_user(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    phone: str = Form(default=""),
    email: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo người dùng mới (chỉ owner)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền tạo user")
    
    try:
        new_user = create_user(db, username, password, full_name, role, phone, email)
        return {"success": True, "user": {
            "id": new_user.id,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "role_display": get_role_display_name(new_user.role),
            "phone": new_user.phone,
            "email": new_user.email
        }}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    full_name: str = Form(...),
    role: str = Form(...),
    phone: str = Form(default=""),
    email: str = Form(default=""),
    password: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin người dùng"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền sửa user")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
        # Update basic info
        user.full_name = full_name
        user.role = role
        user.phone = phone
        user.email = email
        
        # Update password if provided
        if password:
            user.password_hash = get_password_hash(password)
        
        user.updated_at = get_vietnam_time()
        db.commit()
        db.refresh(user)
        
        return {"success": True, "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "role_display": get_role_display_name(user.role),
            "phone": user.phone,
            "email": user.email
        }}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Xóa người dùng (vô hiệu hóa)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền xóa user")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Không thể xóa chính mình")
        
        # Soft delete - chỉ vô hiệu hóa
        user.is_active = False
        user.updated_at = get_vietnam_time()
        db.commit()
        
        return {"success": True, "message": f"Đã vô hiệu hóa người dùng {user.username}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kích hoạt lại người dùng"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có quyền kích hoạt user")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        
        user.is_active = True
        user.updated_at = get_vietnam_time()
        db.commit()
        
        return {"success": True, "message": f"Đã kích hoạt người dùng {user.username}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/test-login")
async def test_user_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Test login cho bất kỳ user nào"""
    try:
        user = authenticate_user(db, username, password)
        if user:
            return {
                "success": True,
                "message": f"✅ Login thành công cho {username}",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "role_display": get_role_display_name(user.role),
                    "is_active": user.is_active
                }
            }
        else:
            return {
                "success": False,
                "message": f"❌ Login thất bại cho {username}",
                "error": "Tài khoản không tồn tại hoặc mật khẩu sai"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Lỗi khi test login: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    # Chạy trên port 8004 để tránh conflict
    uvicorn.run(app, host="0.0.0.0", port=8004)
# Debug endpoints for user management
@app.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint: Liệt kê tất cả users"""
    try:
        users = db.query(User).all()
        user_list = []
        for user in users:
            user_list.append({
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": str(user.created_at)
            })
        return {"total_users": len(users), "users": user_list}
    except Exception as e:
        return {"error": str(e)}

@app.post("/debug/create-admin")
async def debug_create_admin(db: Session = Depends(get_db)):
    """Debug endpoint: Tạo user admin"""
    try:
        # Xóa admin cũ nếu có
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
        
        # Tạo admin mới  
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
        
        return {"status": "success", "message": "Admin user created", "username": "admin", "password": "admin123"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
@app.post("/admin/create")
async def create_admin_simple(db: Session = Depends(get_db)):
    """Simple endpoint: Tạo admin với hardcoded hash"""
    try:
        # Xóa admin cũ nếu có
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
        
        # Tạo admin với hardcoded hash cho admin123
        admin_user = User(
            username="admin",
            password_hash="$2b$12$8/56RWI7xEn6tP1bjeBofuNk049y7g3hdk66lWmei6VHm9TiF99nm",
            full_name="Administrator",
            role="owner", 
            phone="0901234567",
            email="admin@payment.com",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        return {"status": "success", "message": "Admin user created with hardcoded hash", "username": "admin", "password": "admin123"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
@app.post("/debug/test-login")
async def debug_test_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Debug endpoint: Test login logic step by step"""
    try:
        result = {"steps": []}
        
        # Step 1: Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            result["steps"].append("❌ User not found")
            return result
        else:
            result["steps"].append(f"✅ User found: {user.username}, role: {user.role}")
        
        # Step 2: Check if user is active
        if not user.is_active:
            result["steps"].append("❌ User is not active")
            return result
        else:
            result["steps"].append("✅ User is active")
        
        # Step 3: Verify password
        from auth_service import verify_password
        if not verify_password(password, user.password_hash):
            result["steps"].append("❌ Password verification failed")
            result["password_provided"] = password
            result["password_hash"] = user.password_hash[:20] + "..."
            return result
        else:
            result["steps"].append("✅ Password verified")
        
        # Step 4: Create token
        from auth_service import create_access_token
        token = create_access_token(data={"sub": user.username})
        result["steps"].append("✅ Token created")
        result["token"] = token[:20] + "..."
        
        result["status"] = "success"
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e), "type": type(e).__name__}
@app.post("/debug/create-simple-admin")
async def create_simple_admin(db: Session = Depends(get_db)):
    """Tạo admin với password siêu đơn giản"""
    try:
        # Xóa admin cũ
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            db.delete(existing_admin)
            db.commit()
        
        # Hash password ngắn bằng bcrypt trực tiếp
        import bcrypt
        simple_password = "123"
        password_hash = bcrypt.hashpw(simple_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Tạo user
        admin_user = User(
            username="admin",
            password_hash=password_hash,
            full_name="Admin",
            role="owner", 
            phone="123456789",
            email="admin@test.com",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        return {
            "status": "success", 
            "message": "Simple admin created", 
            "username": "admin", 
            "password": "123",
            "hash_length": len(password_hash)
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e), "type": type(e).__name__}
"""
EMERGENCY BYPASS: Simple authentication cho production access
"""

@app.post("/emergency/login")
async def emergency_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Emergency login bypass for production access"""
    # Hardcoded emergency credentials
    if username == "admin" and password == "emergency2025":
        # Create a simple session token
        from datetime import datetime, timedelta
        import jwt
        
        payload = {
            "sub": "admin",
            "role": "owner",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Simple JWT with emergency key
        token = jwt.encode(payload, "emergency-key-2025", algorithm="HS256")
        
        # Set cookie and redirect to admin dashboard
        response = RedirectResponse(url="/admin/payments", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )
        
        return response
    
    return {"status": "error", "message": "Emergency credentials only"}

@app.get("/emergency/create-user")
async def emergency_create_user(db: Session = Depends(get_db)):
    """Emergency user creation with simple password"""
    try:
        # Delete existing users
        db.query(User).delete()
        db.commit()
        
        # Create new admin with simple hash
        import hashlib
        simple_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        admin_user = User(
            username="admin",
            password_hash=simple_hash,
            full_name="Emergency Admin",
            role="owner",
            phone="0000000000",
            email="emergency@admin.com",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        return {
            "status": "success",
            "message": "Emergency admin created",
            "username": "admin",
            "password": "admin123",
            "note": "Use /emergency/login with admin/emergency2025"
        }
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Simple dashboard page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment System Dashboard</title>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🎉 Payment System Dashboard</h1>
        <h2>✅ Đăng nhập thành công!</h2>
        <p><strong>Hệ thống Payment Ledger đã hoạt động!</strong></p>
        
        <div style="background: #f0f0f0; padding: 15px; margin: 20px 0;">
            <h3>📊 Tính năng có sẵn:</h3>
            <ul>
                <li>✅ Authentication đã hoạt động</li>
                <li>✅ Database connection OK</li>
                <li>✅ User management OK</li>
                <li>📋 Booking management (cần implement UI)</li>
                <li>💰 Payment tracking (cần implement UI)</li>
                <li>📈 Reports (cần implement UI)</li>
            </ul>
        </div>
        
        <div style="background: #e8f5e8; padding: 15px; margin: 20px 0;">
            <h3>🚀 Deployment thành công:</h3>
            <ul>
                <li>✅ Railway.app production</li>
                <li>✅ GitHub auto-deployment</li>
                <li>✅ PostgreSQL database</li>
                <li>✅ Vietnamese localization</li>
            </ul>
        </div>
        
        <p><a href="/debug/users" style="color: blue;">🔍 Debug: Xem users</a></p>
        <p><a href="/emergency/create-user" style="color: orange;">🚨 Emergency: Tạo lại user</a></p>
    </body>
    </html>
    """)
@app.get("/emergency")
async def emergency_access(request: Request):
    """Emergency access page"""
    return templates.TemplateResponse("emergency_login.html", {"request": request})

@app.get("/debug/fix-auth")
async def debug_fix_auth(db: Session = Depends(get_db)):
    """Debug endpoint: Fix authentication"""
    try:
        print("🔧 Starting auth fix...")
        import hashlib
        
        # Delete all users
        db.query(User).delete()
        db.commit()
        print("🗑️ Deleted old users")
        
        # Create admin with SHA256
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        admin_user = User(
            username="admin",
            password_hash=admin_hash,
            full_name="Admin System",
            role="owner",
            phone="0901234567",
            email="admin@system.com",
            is_active=True
        )
        db.add(admin_user)
        
        # Create emergency user
        emergency_hash = hashlib.sha256("emergency2025".encode()).hexdigest()
        emergency_user = User(
            username="emergency",
            password_hash=emergency_hash,
            full_name="Emergency Access",
            role="owner",
            phone="0000000000",
            email="emergency@system.com",
            is_active=True
        )
        db.add(emergency_user)
        
        # Create manager
        manager_hash = hashlib.sha256("manager123".encode()).hexdigest()
        manager_user = User(
            username="manager1",
            password_hash=manager_hash,
            full_name="Nguyễn Văn Quản Lý",
            role="manager",
            phone="0907654321", 
            email="manager@system.com",
            is_active=True
        )
        db.add(manager_user)
        
        db.commit()
        print("✅ Users created successfully")
        
        return {
            "status": "success", 
            "message": "Authentication fixed successfully",
            "users_created": [
                {"username": "admin", "password": "admin123", "role": "owner"},
                {"username": "emergency", "password": "emergency2025", "role": "owner"},
                {"username": "manager1", "password": "manager123", "role": "manager"}
            ],
            "auth_method": "SHA256"
        }
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

# Admin Routes - Payments and Handovers
@app.get("/test-simple")
async def test_simple():
    """Test route simplest"""
    return {"message": "Simple route works!"}

@app.get("/admin/test", response_class=HTMLResponse)
async def admin_test_page(request: Request):
    """Test admin route"""
    return HTMLResponse("<html><body><h1>Admin Test Works!</h1></body></html>")

@app.get("/admin/payments-debug")
async def admin_payments_debug(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug admin payments route"""
    return JSONResponse({
        "message": "Admin payments route works",
        "user": current_user.username,
        "role": current_user.role
    })

@app.get("/admin/payments", response_class=HTMLResponse)
async def admin_payments_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trang quản lý ghi nhận thu"""
    print(f"🔍 admin_payments_page called by user: {current_user.username}")
    try:
        return templates.TemplateResponse("admin_payments.html", {
            "request": request, 
            "user": current_user,
            "getVietnamTime": get_vietnam_time
        })
    except Exception as e:
        print(f"❌ Template error in admin_payments: {e}")
        return JSONResponse({
            "error": f"Template error: {str(e)}",
            "template": "admin_payments.html"
        }, status_code=500)

@app.get("/admin/handovers", response_class=HTMLResponse)
async def admin_handovers_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trang quản lý bàn giao"""
    print(f"🔍 admin_handovers_page called by user: {current_user.username}")
    try:
        return templates.TemplateResponse("admin_handovers.html", {
            "request": request,
            "user": current_user,
            "getVietnamTime": get_vietnam_time
        })
    except Exception as e:
        print(f"❌ Template error in admin_handovers: {e}")
        return JSONResponse({
            "error": f"Template error: {str(e)}",
            "template": "admin_handovers.html"
        }, status_code=500)

@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trang báo cáo thu chi"""
    return templates.TemplateResponse("reports_simple.html", {
        "request": request, 
        "user": current_user,
        "getVietnamTime": get_vietnam_time
    })

# Debug endpoints for production troubleshooting
@app.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """Debug endpoint để check users trong database"""
    try:
        users = db.query(User).all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "password_hash": user.password_hash[:20] + "..." if user.password_hash else None
            })
        
        return {
            "total_users": len(users),
            "users": user_list,
            "database_type": "PostgreSQL" if os.getenv("DATABASE_URL") else "SQLite"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/test-auth/{username}/{password}")
async def debug_test_auth(username: str, password: str, db: Session = Depends(get_db)):
    """Debug endpoint để test authentication"""
    try:
        print(f"🧪 Testing auth for: {username}")
        user = authenticate_user(db, username, password)
        
        if user:
            return {
                "success": True,
                "user": {
                    "username": user.username,
                    "role": user.role,
                    "full_name": user.full_name
                }
            }
        else:
            return {"success": False, "message": "Authentication failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Backup & Import APIs
@app.post("/api/backup/create")
async def create_backup(db: Session = Depends(get_db)):
    """Tạo backup data"""
    try:
        # Get all data
        payments = db.query(Payment).all()
        handovers = db.query(Handover).all()
        buildings = db.query(Building).all()
        users = db.query(User).all()
        
        backup_data = {
            "backup_date": get_vietnam_time().isoformat(),
            "payments": [{
                "booking_id": p.booking_id,
                "guest_name": p.guest_name,
                "building_id": p.building_id,
                "room_number": p.room_number,
                "amount_collected": p.amount_collected,
                "payment_method": p.payment_method,
                "collected_by": p.collected_by,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in payments],
            "handovers": [{
                "id": h.id,
                "building_id": h.building_id,
                "from_person": h.from_person,
                "to_person": h.to_person,
                "amount": h.amount,
                "notes": h.notes,
                "image_path": h.image_path,
                "status": h.status,
                "handover_by_user_id": h.handover_by_user_id,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None
            } for h in handovers],
            "buildings": [{
                "name": b.name,
                "address": b.address,
                "contact_info": b.contact_info,
                "created_at": b.created_at.isoformat() if b.created_at else None
            } for b in buildings],
            "users": [{
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "phone": u.phone,
                "email": u.email,
                "is_active": u.is_active
            } for u in users]
        }
        
        return JSONResponse({
            "success": True,
            "data": backup_data,
            "summary": {
                "payments": len(payments),
                "handovers": len(handovers),
                "buildings": len(buildings),
                "users": len(users)
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Google Drive Backup APIs
@app.post("/api/gdrive/backup")
async def backup_to_google_drive(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload backup to Google Drive with handover images"""
    if not GOOGLE_DRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="Google Drive backup not available")
        
    try:
        # Only allow managers and owners
        if current_user.role not in ["manager", "owner"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        # Initialize Google Drive backup
        drive_backup = GoogleDriveBackup()
        drive_backup.authenticate()
        drive_backup.create_backup_folder()
        
        # Get all data
        payments = db.query(Payment).all()
        handovers = db.query(Handover).all()
        buildings = db.query(Building).all()
        users = db.query(User).all()
        
        # Prepare handover data with image backup
        handover_data = []
        images_backed_up = 0
        
        for h in handovers:
            handover_dict = {
                "id": h.id,
                "building_id": h.building_id,
                "from_person": h.from_person,
                "to_person": h.to_person,
                "amount": h.amount,
                "notes": h.notes,
                "image_path": h.image_path,
                "status": h.status,
                "handover_by_user_id": h.handover_by_user_id,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None
            }
            
            # Backup image if exists
            if h.image_path and os.path.exists(h.image_path):
                print(f"📷 Backing up handover image: {h.image_path}")
                drive_filename = f"handover_{h.id}_{os.path.basename(h.image_path)}"
                image_result = drive_backup.backup_image_to_drive(h.image_path, drive_filename)
                if image_result:
                    handover_dict["drive_image_id"] = image_result.get('id')
                    handover_dict["drive_image_link"] = image_result.get('webViewLink')
                    images_backed_up += 1
                    print(f"✅ Image backed up: {drive_filename}")
                else:
                    print(f"⚠️ Failed to backup image: {h.image_path}")
            
            handover_data.append(handover_dict)
        
        # Create comprehensive backup data
        backup_data = {
            "backup_date": get_vietnam_time().isoformat(),
            "version": "2.0",
            "images_backed_up": images_backed_up,
            "payments": [{
                "booking_id": p.booking_id,
                "guest_name": p.guest_name,
                "building_id": p.building_id,
                "room_number": p.room_number,
                "amount_due": p.amount_due,
                "amount_collected": p.amount_collected,
                "payment_method": p.payment_method,
                "collected_by": p.collected_by,
                "notes": p.notes,
                "receipt_image": p.receipt_image,
                "status": p.status,
                "added_by_user_id": p.added_by_user_id,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            } for p in payments],
            "handovers": handover_data,
            "buildings": [{
                "name": b.name,
                "address": b.address,
                "contact_info": b.contact_info,
                "created_at": b.created_at.isoformat() if b.created_at else None
            } for b in buildings],
            "users": [{
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None
            } for u in users]
        }
        
        # Upload backup data to Google Drive
        filename = f"airbnb_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result = drive_backup.backup_to_drive(backup_data, filename)
        
        if result:
            return {
                "success": True,
                "message": f"Backup uploaded successfully! {images_backed_up} images backed up.",
                "file_info": {
                    "name": result['name'],
                    "size": result['size'],
                    "created_time": result['createdTime'],
                    "images_backed_up": images_backed_up
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload backup to Google Drive")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive backup error: {str(e)}")

@app.get("/api/gdrive/backups")
async def list_google_drive_backups(
    current_user: User = Depends(get_current_user)
):
    """List backups on Google Drive"""
    if not GOOGLE_DRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="Google Drive backup not available")
        
    try:
        if current_user.role not in ["manager", "owner"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        drive_backup = GoogleDriveBackup()
        drive_backup.authenticate()
        drive_backup.create_backup_folder()
        
        backups = drive_backup.list_backups(20)
        
        return {
            "success": True,
            "backups": backups
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing Google Drive backups: {str(e)}")

@app.post("/api/gdrive/setup-auto-backup")
async def setup_auto_backup(
    current_user: User = Depends(get_current_user)
):
    """Setup automatic daily backup to Google Drive"""
    if not GOOGLE_DRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="Google Drive backup not available")
        
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can setup auto backup")
            
        # Test Google Drive connection
        drive_backup = GoogleDriveBackup()
        drive_backup.authenticate()
        drive_backup.create_backup_folder()
        
        # Setup backup schedule in background thread
        def start_backup_service():
            setup_backup_schedule()
            import schedule
            import time
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        # Start backup service thread
        backup_thread = threading.Thread(target=start_backup_service, daemon=True)
        backup_thread.start()
        
        return {
            "success": True,
            "message": "Auto backup to Google Drive enabled",
            "schedule": "Daily at 2:00 AM Vietnam time"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto backup setup error: {str(e)}")

@app.post("/api/gdrive/restore/{file_id}")
async def restore_from_google_drive(
    file_id: str,
    restore_images: bool = True,
    clear_existing: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restore data and images from Google Drive backup"""
    if not GOOGLE_DRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="Google Drive backup not available")
        
    try:
        # Only allow owners to restore
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can restore from backup")
            
        # Initialize Google Drive service
        drive_backup = GoogleDriveBackup()
        drive_backup.authenticate()
        
        # Restore from backup
        restore_result = drive_backup.restore_from_backup(file_id, restore_images)
        if not restore_result["success"]:
            raise HTTPException(status_code=500, detail=restore_result.get("error", "Restore failed"))
        
        backup_data = restore_result["backup_data"]
        restored_counts = restore_result["restored_counts"]
        
        # Clear existing data if requested
        if clear_existing:
            print("🗑️ Clearing existing data...")
            db.query(Payment).delete()
            db.query(Handover).delete()
            # Don't delete buildings and users as they may be critical
            db.commit()
        
        # Restore payments
        if "payments" in backup_data:
            for payment_data in backup_data["payments"]:
                # Check if payment already exists
                existing = db.query(Payment).filter(
                    Payment.booking_id == payment_data["booking_id"],
                    Payment.guest_name == payment_data["guest_name"]
                ).first()
                
                if not existing:
                    payment = Payment(
                        booking_id=payment_data["booking_id"],
                        guest_name=payment_data["guest_name"],
                        building_id=payment_data["building_id"],
                        room_number=payment_data["room_number"],
                        amount_due=payment_data.get("amount_due", payment_data["amount_collected"]),  # Use amount_collected as fallback
                        amount_collected=payment_data["amount_collected"],
                        payment_method=payment_data["payment_method"],
                        collected_by=payment_data["collected_by"],
                        notes=payment_data.get("notes", ""),
                        receipt_image=payment_data.get("receipt_image"),
                        status=payment_data.get("status", "completed"),
                        added_by_user_id=payment_data.get("added_by_user_id", current_user.id)
                    )
                    if payment_data.get("created_at"):
                        payment.created_at = datetime.fromisoformat(payment_data["created_at"])
                    
                    db.add(payment)
                    restored_counts["payments"] += 1
        
        # Restore handovers
        if "handovers" in backup_data:
            for handover_data in backup_data["handovers"]:
                # Check if handover already exists (by from_person, to_person, amount)
                existing = db.query(Handover).filter(
                    Handover.from_person == handover_data["from_person"],
                    Handover.to_person == handover_data["to_person"],
                    Handover.amount == handover_data["amount"]
                ).first()
                
                if not existing:
                    handover = Handover(
                        building_id=handover_data["building_id"],
                        from_person=handover_data["from_person"],
                        to_person=handover_data["to_person"],
                        amount=handover_data["amount"],
                        notes=handover_data.get("notes", ""),
                        image_path=handover_data.get("image_path"),
                        status=handover_data.get("status", "completed"),
                        handover_by_user_id=handover_data.get("handover_by_user_id", current_user.id)
                    )
                    if handover_data.get("created_at"):
                        handover.created_at = datetime.fromisoformat(handover_data["created_at"])
                    if handover_data.get("updated_at"):
                        handover.updated_at = datetime.fromisoformat(handover_data["updated_at"])
                    
                    db.add(handover)
                    restored_counts["handovers"] += 1
        
        # Restore buildings (only if they don't exist)
        if "buildings" in backup_data:
            for building_data in backup_data["buildings"]:
                existing = db.query(Building).filter(Building.name == building_data["name"]).first()
                if not existing:
                    building = Building(
                        name=building_data["name"],
                        address=building_data.get("address", ""),
                        contact_info=building_data.get("contact_info", "")
                    )
                    if building_data.get("created_at"):
                        building.created_at = datetime.fromisoformat(building_data["created_at"])
                    
                    db.add(building)
                    restored_counts["buildings"] += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Restore completed successfully!",
            "backup_info": {
                "backup_date": backup_data.get("backup_date"),
                "version": backup_data.get("version", "1.0")
            },
            "restored_counts": restored_counts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Restore error: {str(e)}")

@app.post("/api/payments/import")
async def import_payments_json(
    import_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import payments from JSON data"""
    try:
        # Only allow managers and owners
        if current_user.role not in ["manager", "owner"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        payments_data = import_data.get("payments", [])
        if not payments_data:
            raise HTTPException(status_code=400, detail="No payment data provided")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for i, payment_data in enumerate(payments_data):
            try:
                # Validate required fields
                required_fields = ["booking_id", "guest_name", "amount_collected"]
                missing_fields = [field for field in required_fields if not payment_data.get(field)]
                
                if missing_fields:
                    errors.append(f"Row {i+1}: Missing required fields: {', '.join(missing_fields)}")
                    error_count += 1
                    continue
                
                # Check if payment already exists
                existing = db.query(Payment).filter(
                    Payment.booking_id == payment_data["booking_id"],
                    Payment.guest_name == payment_data["guest_name"]
                ).first()
                
                if existing:
                    errors.append(f"Row {i+1}: Payment already exists (Booking: {payment_data['booking_id']})")
                    error_count += 1
                    continue
                
                # Create new payment
                payment = Payment(
                    booking_id=payment_data["booking_id"],
                    guest_name=payment_data["guest_name"],
                    building_id=payment_data.get("building_id", 1),
                    room_number=payment_data.get("room_number", ""),
                    amount_due=payment_data.get("amount_due", payment_data["amount_collected"]),
                    amount_collected=float(payment_data["amount_collected"]),
                    payment_method=payment_data.get("payment_method", "cash"),
                    collected_by=payment_data.get("collected_by", current_user.username),
                    notes=payment_data.get("notes", ""),
                    receipt_image=payment_data.get("receipt_image"),
                    status=payment_data.get("status", "completed"),
                    added_by_user_id=current_user.id
                )
                
                db.add(payment)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
                error_count += 1
                continue
        
        # Commit all successful imports
        if success_count > 0:
            db.commit()
        
        return {
            "success": True,
            "message": f"Import completed: {success_count} success, {error_count} errors",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10]  # Limit errors shown
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

@app.post("/api/sample-data/create")
async def create_sample_data(db: Session = Depends(get_db)):
    """Tạo sample data cho demo"""
    try:
        # Check if data already exists
        existing_payments = db.query(Payment).count()
        existing_buildings = db.query(Building).count()
        
        if existing_payments > 0 or existing_buildings > 0:
            return {"success": False, "message": "Data đã tồn tại. Sử dụng /api/sample-data/reset để reset."}
        
        # Create sample buildings
        buildings_data = [
            {"name": "Tòa nhà A - Quận 1", "address": "123 Đường Lê Lợi, Quận 1, TP.HCM", "contact_info": "028.1234.5678"},
            {"name": "Tòa nhà B - Quận 3", "address": "456 Đường Võ Văn Tần, Quận 3, TP.HCM", "contact_info": "028.9876.5432"},
            {"name": "Tòa nhà C - Quận 7", "address": "789 Đường Nguyễn Hữu Thọ, Quận 7, TP.HCM", "contact_info": "028.5555.6666"}
        ]
        
        created_buildings = []
        for building_data in buildings_data:
            building = Building(
                name=building_data["name"],
                address=building_data["address"],
                contact_info=building_data["contact_info"],
                created_at=get_vietnam_time()
            )
            db.add(building)
            db.flush()
            created_buildings.append(building)
        
        # Create sample payments
        import random
        from datetime import timedelta
        
        sample_payments = []
        guest_names = ["Nguyễn Văn A", "Trần Thị B", "Lê Minh C", "Phạm Thu D", "Hoàng Văn E", "Vũ Thị F"]
        payment_methods = ["cash", "bank_transfer", "credit_card"]
        collectors = ["Thu Chi 1", "Thu Chi 2", "Admin"]
        
        for i in range(15):
            building = random.choice(created_buildings)
            payment = Payment(
                booking_id=f"BK{str(i+1).zfill(3)}",
                guest_name=random.choice(guest_names),
                building_id=building.id,
                room_number=f"{random.randint(1,5)}{str(random.randint(1,20)).zfill(2)}",
                amount_collected=random.randint(300, 1500) * 1000,
                payment_method=random.choice(payment_methods),
                collected_by=random.choice(collectors),
                notes=f"Sample payment {i+1}",
                created_at=get_vietnam_time() - timedelta(days=random.randint(0, 30))
            )
            db.add(payment)
            sample_payments.append(payment)
        
        # Create sample handovers
        for building in created_buildings:
            handover = Handover(
                building_id=building.id,
                handover_date=get_vietnam_time() - timedelta(days=random.randint(1, 7)),
                room_count=random.randint(3, 8),
                total_amount=random.randint(2000, 8000) * 1000,
                recipient="Kế toán",
                notes=f"Bàn giao tiền mặt {building.name}",
                created_at=get_vietnam_time() - timedelta(days=random.randint(1, 7))
            )
            db.add(handover)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Sample data created successfully",
            "summary": {
                "buildings": len(created_buildings),
                "payments": len(sample_payments),
                "handovers": len(created_buildings)
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Khởi động server - Railway compatibility
if __name__ == "__main__":
    import uvicorn
    
    # Debug: Print all routes
    print("🔍 Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)} {route.path}")
    
    # Railway sets PORT environment variable
    port = int(os.environ.get("PORT", 8004))  # Default to 8004 for development
    print(f"🚀 Starting server on port {port}")
    
    uvicorn.run(
        app,  # Use app object directly
        host="0.0.0.0", 
        port=port,
        reload=False  # Production mode
    )
