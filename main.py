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

# Import các module tự tạo
from database_production import get_db, create_tables, User, Payment, Handover  
from auth_service import (
    authenticate_user, 
    create_access_token, 
    get_current_user_from_token,
    create_user,
    get_all_users,
    get_role_display_name
)

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

# Add helper to template globals
templates.env.globals['getRoleDisplayName'] = get_role_display_name_helper

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
            return templates.TemplateResponse("payment_complete.html", {
                "request": request,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role
                },
                "getRoleDisplayName": get_role_display_name_helper
            })
        else:
            print("Token verification failed: user not found")
    except Exception as e:
        print(f"Token verification failed with error: {e}")
    
    # Redirect to login if no valid token
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Trang đăng nhập"""
    return templates.TemplateResponse("login_production.html", {"request": request})

@app.get("/debug", response_class=HTMLResponse)
async def debug_page(request: Request):
    """Debug authentication page"""
    return templates.TemplateResponse("debug_auth.html", {"request": request})

@app.get("/api/test-auth")
async def test_auth(request: Request, db: Session = Depends(get_db)):
    """Test authentication"""
    token = request.cookies.get("access_token")
    if not token:
        return {"status": "no_token"}
    
    try:
        user = get_current_user_from_token(token, db)
        if user:
            return {
                "status": "authenticated",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role
                }
            }
        else:
            return {"status": "invalid_token"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Đăng nhập API"""
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không đúng")
    
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
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=1440*60,  # 24 giờ
        secure=False  # Đặt True khi deploy HTTPS
    )
    
    return response

@app.post("/api/payments")
async def add_payment(
    request: Request,
    booking_id: str = Form(...),
    guest_name: str = Form(...),
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
    
    # Tạo payment record
    payment = Payment(
        booking_id=booking_id,
        guest_name=guest_name,
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
        "created_at": payment.created_at.isoformat()
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
        payments_data.append({
            "id": payment.id,
            "booking_id": payment.booking_id,
            "guest_name": payment.guest_name,
            "amount_due": payment.amount_due,
            "amount_collected": payment.amount_collected,
            "payment_method": payment.payment_method,
            "collected_by": payment.collected_by,
            "notes": payment.notes,
            "receipt_image": payment.receipt_image,
            "status": payment.status,
            "created_at": payment.created_at.isoformat(),
            "timestamp": payment.created_at.isoformat()
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
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/handovers")
async def create_handover(
    request: Request,
    recipient_user_id: int = Form(...),
    amount: float = Form(...),
    notes: str = Form(default=""),
    handover_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tạo bàn giao tiền mặt"""
    
    # Kiểm tra người nhận có tồn tại không
    recipient = db.query(User).filter(User.id == recipient_user_id, User.is_active == True).first()
    if not recipient:
        raise HTTPException(status_code=400, detail="Không tìm thấy người nhận")
    
    # Xử lý upload hình ảnh bàn giao
    image_path = None
    if handover_image and handover_image.filename:
        file_extension = handover_image.filename.split('.')[-1]
        unique_filename = f"handover_{uuid.uuid4()}.{file_extension}"
        image_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(handover_image.file, buffer)
        
        image_path = f"/uploads/{unique_filename}"
    
    # Tạo handover record
    handover = Handover(
        handover_by_user_id=current_user.id,
        recipient_user_id=recipient_user_id,
        amount=amount,
        notes=notes,
        handover_image=image_path,
        status="completed",
        signature_status="pending"
    )
    
    db.add(handover)
    db.commit()
    db.refresh(handover)
    
    return {"success": True, "handover": {
        "id": handover.id,
        "handover_by": current_user.full_name,
        "recipient_name": recipient.full_name,
        "recipient_phone": recipient.phone,
        "amount": handover.amount,
        "notes": handover.notes,
        "handover_image": handover.handover_image,
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
        recipient_user = db.query(User).filter(User.id == handover.recipient_user_id).first()
        
        handovers_data.append({
            "id": handover.id,
            "handover_by": handover_by_user.full_name if handover_by_user else "Unknown",
            "recipient_name": recipient_user.full_name if recipient_user else "Unknown",
            "recipient_phone": recipient_user.phone if recipient_user else "",
            "amount": handover.amount,
            "notes": handover.notes,
            "handover_image": handover.handover_image,
            "status": handover.status,
            "signature_status": handover.signature_status,
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

@app.post("/api/logout")
async def logout(request: Request):
    """Đăng xuất"""
    response = JSONResponse({"success": True})
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
    
    return templates.TemplateResponse("admin_users.html", {"request": request})

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

if __name__ == "__main__":
    import uvicorn
    # Chạy trên port 8004 để tránh conflict
    uvicorn.run(app, host="0.0.0.0", port=8004)
@ a p p . g e t ( " / d e b u g / u s e r s " ) 
 a s y n c   d e f   d e b u g _ u s e r s ( d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ) : 
         " " " D e b u g   e n d p o i n t :   L i �t   k �   t �t   c �  u s e r s " " " 
         t r y : 
                 u s e r s   =   d b . q u e r y ( U s e r ) . a l l ( ) 
                 u s e r _ l i s t   =   [ ] 
                 f o r   u s e r   i n   u s e r s : 
                         u s e r _ l i s t . a p p e n d ( { 
                                 " u s e r n a m e " :   u s e r . u s e r n a m e , 
                                 " r o l e " :   u s e r . r o l e , 
                                 " i s _ a c t i v e " :   u s e r . i s _ a c t i v e , 
                                 " c r e a t e d _ a t " :   s t r ( u s e r . c r e a t e d _ a t ) 
                         } ) 
                 r e t u r n   { " t o t a l _ u s e r s " :   l e n ( u s e r s ) ,   " u s e r s " :   u s e r _ l i s t } 
         e x c e p t   E x c e p t i o n   a s   e : 
                 r e t u r n   { " e r r o r " :   s t r ( e ) } 
 
 @ a p p . p o s t ( " / d e b u g / c r e a t e - a d m i n " ) 
 a s y n c   d e f   d e b u g _ c r e a t e _ a d m i n ( d b :   S e s s i o n   =   D e p e n d s ( g e t _ d b ) ) : 
         " " " D e b u g   e n d p o i n t :   T �o   u s e r   a d m i n " " " 
         t r y : 
                 #   X � a   a d m i n   c i  n �u   c � 
                 e x i s t i n g _ a d m i n   =   d b . q u e r y ( U s e r ) . f i l t e r ( U s e r . u s e r n a m e   = =   " a d m i n " ) . f i r s t ( ) 
                 i f   e x i s t i n g _ a d m i n : 
                         d b . d e l e t e ( e x i s t i n g _ a d m i n ) 
                         d b . c o m m i t ( ) 
                 
                 #   T �o   a d m i n   m �i     
                 a d m i n _ u s e r   =   U s e r ( 
                         u s e r n a m e = " a d m i n " , 
                         p a s s w o r d _ h a s h = g e t _ p a s s w o r d _ h a s h ( " a d m i n 1 2 3 " ) , 
                         f u l l _ n a m e = " A d m i n i s t r a t o r " , 
                         r o l e = " o w n e r " ,   
                         p h o n e = " 0 9 0 1 2 3 4 5 6 7 " , 
                         e m a i l = " a d m i n @ p a y m e n t . c o m " , 
                         i s _ a c t i v e = T r u e 
                 ) 
                 
                 d b . a d d ( a d m i n _ u s e r ) 
                 d b . c o m m i t ( ) 
                 
                 r e t u r n   { " s t a t u s " :   " s u c c e s s " ,   " m e s s a g e " :   " A d m i n   u s e r   c r e a t e d " ,   " u s e r n a m e " :   " a d m i n " ,   " p a s s w o r d " :   " a d m i n 1 2 3 " } 
         e x c e p t   E x c e p t i o n   a s   e : 
                 d b . r o l l b a c k ( ) 
                 r e t u r n   { " s t a t u s " :   " e r r o r " ,   " m e s s a g e " :   s t r ( e ) }  
 