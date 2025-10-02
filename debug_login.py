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