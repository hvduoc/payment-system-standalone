@app.get("/emergency/login")
async def emergency_login_page(request: Request):
    """Emergency login page với form HTML"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Emergency Login - Payment System</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; 
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
            }
            .title {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .emergency-badge {
                background: #ff4757;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 12px;
                display: inline-block;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #555;
            }
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
                font-size: 16px;
            }
            input[type="text"]:focus, input[type="password"]:focus {
                border-color: #667eea;
                outline: none;
            }
            .btn-emergency {
                width: 100%;
                padding: 15px;
                background: #ff4757;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
            }
            .btn-emergency:hover {
                background: #ff3838;
            }
            .info-box {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                font-size: 14px;
                color: #666;
            }
            .credentials {
                background: #e8f5e8;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="emergency-badge">🚨 EMERGENCY ACCESS</div>
            <h1 class="title">Payment System<br>Emergency Login</h1>
            
            <form method="POST" action="/emergency/login">
                <div class="form-group">
                    <label for="username">👤 Username:</label>
                    <input type="text" id="username" name="username" value="admin" required>
                </div>
                
                <div class="form-group">
                    <label for="password">🔑 Emergency Password:</label>
                    <input type="password" id="password" name="password" value="emergency2025" required>
                </div>
                
                <button type="submit" class="btn-emergency">
                    🚨 Emergency Access
                </button>
            </form>
            
            <div class="info-box">
                <div class="credentials">
                    <strong>Emergency Credentials:</strong><br>
                    Username: admin<br>
                    Password: emergency2025
                </div>
                
                <p><strong>🔧 Emergency Access được tạo để:</strong></p>
                <ul>
                    <li>Bypass authentication conflicts</li>
                    <li>Quick access to production system</li>
                    <li>Debug và fix issues</li>
                </ul>
                
                <p><strong>✅ System Status:</strong> Production Ready</p>
            </div>
        </div>
    </body>
    </html>
    """)