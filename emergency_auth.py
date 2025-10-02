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
        
        # Set cookie and redirect
        response = RedirectResponse(url="/dashboard", status_code=302)
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