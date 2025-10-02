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