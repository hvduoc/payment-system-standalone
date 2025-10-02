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