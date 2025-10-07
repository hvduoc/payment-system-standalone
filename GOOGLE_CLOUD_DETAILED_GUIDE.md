# 🎯 Hướng dẫn tạo Google Cloud Project từ A-Z

## 📍 Vị trí nút tạo Project

### Cách 1: Từ header chính
1. **Vào https://console.cloud.google.com/**
2. **Tìm dropdown project ở header**:
   ```
   [Google Cloud] [Select a project ▼] [🔔] [👤]
                  ↑
                  Click vào đây
   ```
3. **Trong popup sẽ có**:
   - Danh sách project hiện có
   - Nút **"NEW PROJECT"** ở góc trên phải của popup

### Cách 2: Từ IAM & Admin
1. **Menu bên trái** > **"IAM & Admin"** > **"Manage Resources"**
2. Click **"CREATE PROJECT"** ở trên cùng

### Cách 3: Direct link
- Truy cập trực tiếp: https://console.cloud.google.com/projectcreate

## 🎨 Giao diện tạo project

Khi click "NEW PROJECT", bạn sẽ thấy form:

```
Create a Project
┌─────────────────────────────────────┐
│ Project name: [Airbnb Payment Backup] │
├─────────────────────────────────────┤
│ Project ID: [airbnb-payment-backup-] │ 
│             [auto-generated]        │
├─────────────────────────────────────┤
│ Organization: [No organization ▼]   │
├─────────────────────────────────────┤
│ Location: [No folder ▼]             │
└─────────────────────────────────────┘
               [CREATE]
```

## ⚡ Bước tiếp theo sau khi tạo project

1. **Chờ project được tạo** (vài giây)
2. **Đảm bảo đã chọn đúng project**:
   - Header sẽ hiển thị: `[Google Cloud] [Airbnb Payment Backup ▼]`
3. **Enable Google Drive API**:
   - Menu > "APIs & Services" > "Library"
   - Search "Google Drive API"
   - Click "ENABLE"

## 🚨 Troubleshooting

### Không thấy nút "NEW PROJECT"?
- **Kiểm tra permissions**: Đảm bảo Google account có quyền tạo project
- **Try incognito mode**: Thử dùng chế độ ẩn danh
- **Switch account**: Đổi sang Google account khác nếu có

### Project ID bị trùng?
- Google sẽ tự động thêm số random vào cuối
- VD: `airbnb-payment-backup-123456`
- Không cần thay đổi gì

### Không thấy "APIs & Services"?
- Đảm bảo đã chọn đúng project (tên hiển thị ở header)
- Refresh trang
- Menu có thể bị collapsed, click vào hamburger menu ☰

## 📋 Checklist hoàn thành

- [ ] ✅ Tạo project thành công
- [ ] ✅ Chọn đúng project trong dropdown
- [ ] ✅ Enable Google Drive API
- [ ] ✅ Configure OAuth consent screen  
- [ ] ✅ Tạo OAuth 2.0 credentials
- [ ] ✅ Download credentials.json
- [ ] ✅ Copy file vào project folder

## 🔗 Quick Links

- **Create Project**: https://console.cloud.google.com/projectcreate
- **APIs Library**: https://console.cloud.google.com/apis/library
- **Credentials**: https://console.cloud.google.com/apis/credentials
- **OAuth Consent**: https://console.cloud.google.com/apis/credentials/consent

---

💡 **Tip**: Nếu vẫn không tìm thấy, thử search "create project" trong search box ở Google Cloud Console!