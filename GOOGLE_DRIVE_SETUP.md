# Google Drive Setup Instructions
# Hướng dẫn setup Google Drive API cho auto backup

## Bước 1: Tạo Google Cloud Project
1. Truy cập https://console.cloud.google.com/ (hoặc https://console.developers.google.com/)
2. **Tạo project mới**:
   - Nhìn lên góc trên cùng, bên cạnh "Google Cloud" sẽ có dropdown hiển thị project hiện tại
   - Click vào dropdown đó (có thể hiển thị "Select a project" hoặc tên project hiện tại)
   - Click "NEW PROJECT" ở góc trên bên phải của popup
   - Hoặc click vào icon "Select a project" rồi chọn "New Project"
3. **Điền thông tin project**:
   - Project name: "Airbnb Payment Backup"
   - Organization: để mặc định (No organization)
   - Location: để mặc định
   - Click "CREATE"

## Bước 2: Enable Google Drive API
1. **Đảm bảo đã chọn đúng project** (tên project sẽ hiển thị ở góc trên cùng)
2. Trong Google Cloud Console, vào **"APIs & Services"** > **"Library"**
   - Tìm mục "APIs & Services" ở menu bên trái
   - Click "Library"
3. **Tìm Google Drive API**:
   - Gõ "Google Drive API" vào ô search
   - Click vào "Google Drive API" trong kết quả
4. Click nút **"ENABLE"** màu xanh

## Bước 3: Tạo Credentials
1. Sau khi enable Google Drive API, vào **"APIs & Services"** > **"Credentials"**
2. Click **"CREATE CREDENTIALS"** > **"OAuth 2.0 Client IDs"**
3. **Nếu chưa có OAuth consent screen**:
   - Sẽ có thông báo yêu cầu configure consent screen
   - Click "CONFIGURE CONSENT SCREEN"
   - Chọn "External" > "CREATE"
   - Điền thông tin cơ bản:
     - App name: "Airbnb Payment Backup"
     - User support email: email của bạn
     - Developer contact: email của bạn
   - Click "SAVE AND CONTINUE" qua các bước còn lại
4. **Tạo OAuth 2.0 Client ID**:
   - Quay lại "Credentials" > "CREATE CREDENTIALS" > "OAuth 2.0 Client IDs"
   - Application type: chọn **"Desktop application"**
   - Name: "Airbnb Backup Client"
   - Click **"CREATE"**
5. **Download credentials**:
   - Popup sẽ hiện ra với Client ID và Client Secret
   - Click **"DOWNLOAD JSON"**
   - Đổi tên file thành `credentials.json`
   - Copy file vào thư mục project: `d:\DUAN1\Airbnb\payment-system-standalone\`

## Bước 4: Install Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client schedule
```

## Bước 5: Test Backup
```bash
python google_drive_backup.py
```

## Bước 6: Add vào Railway
1. Upload `credentials.json` vào Railway project
2. Add environment variable:
```
GOOGLE_DRIVE_BACKUP=true
```

## File Structure
```
payment-system-standalone/
├── google_drive_backup.py        # Backup service
├── credentials.json              # Google API credentials (gitignore)
├── token.pickle                  # Auth token (auto-generated)
└── requirements.txt             # Updated dependencies
```

## Automated Schedule
- **Daily backup**: 2:00 AM Vietnam time
- **Weekly full backup**: Sunday 3:00 AM  
- **Retention**: 30 days
- **Storage**: 2TB Google Drive miễn phí

## Backup Structure on Google Drive
```
/Airbnb_Payment_Backups/
├── airbnb_backup_20241211_020000.json
├── airbnb_backup_20241212_020000.json
└── weekly_backup_20241215_030000.json
```

## Integration với Railway
File backup service sẽ chạy như background process trên Railway và tự động:
- Backup daily vào Google Drive
- Cleanup old backups
- Monitor backup status
- Send notifications nếu backup fail