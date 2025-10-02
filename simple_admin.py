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