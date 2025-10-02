# Payment System Standalone 💰

Hệ thống quản lý thu chi Airbnb hoàn toàn độc lập - tách rời từ main project để đảm bảo ổn định.

## 🎯 **Tính năng chính:**

### 💰 **Quản lý Thu Chi**
- Ghi nhận khoản thu với nhiều phương thức thanh toán
- Upload hình ảnh biên lai
- Theo dõi tỷ lệ thu theo thời gian thực

### 🤝 **Bàn giao tiền mặt**
- Quản lý bàn giao tiền mặt giữa các thành viên
- Upload hình ảnh bàn giao
- Theo dõi trạng thái ký nhận

### 👥 **Quản lý người dùng**
- Phân quyền theo vai trò: Admin/Manager/Assistant/Owner
- Giao diện riêng biệt cho từng role
- Bảo mật với JWT token

### 📊 **Dashboard real-time**
- KPIs tự động cập nhật
- Thống kê thu chi theo thời gian
- Giao diện responsive mobile-friendly

## 🛠 **Tech Stack:**

- **Backend**: FastAPI + SQLModel
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: HTML + JavaScript + TailwindCSS
- **Authentication**: JWT + bcrypt
- **Deployment**: Railway.app + Docker

## 🚀 **Deployment trên Railway:**

### **1. Tạo project mới:**
```bash
railway.app → New Project → Deploy from GitHub
```

### **2. Environment Variables:**
```env
SECRET_KEY=airbnb-payment-ledger-secret-key-vietnam-2025
PORT=8000
DATABASE_URL=(Railway tự generate)
```

### **3. Services cần thiết:**
- ✅ Web Service (từ GitHub)
- ✅ PostgreSQL Database

### **4. Demo Users:**
```
admin / admin123 (Owner)
manager1 / manager123 (Manager)
```

## 🎯 **Production Ready Features:**

- ✅ Auto database initialization
- ✅ Demo users tự động tạo
- ✅ PostgreSQL production support
- ✅ Vietnamese interface hoàn chỉnh
- ✅ File upload với preview
- ✅ Role-based access control
- ✅ Real-time dashboard updates
- ✅ Mobile responsive design

## 🔧 **Local Development:**

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Access: http://localhost:8004
```

## 📱 **Usage:**

1. **Đăng nhập** với demo accounts
2. **Ghi nhận thu**: Tab "Ghi nhận thu" 
3. **Bàn giao tiền**: Tab "Bàn giao"
4. **Xem báo cáo**: Dashboard + History tabs
5. **Quản lý team**: Tab "Đội ngũ"

---

**Phát triển bởi**: GitHub Copilot  
**Version**: 2.0 Production  
**Ngày**: 02/10/2025  
**Status**: 🟢 Production Ready