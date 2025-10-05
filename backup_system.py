"""
Backup and Migration Scripts cho Payment System
"""

import os
import shutil
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database_production import get_db, User, Payment, Handover

def backup_database_to_json():
    """Backup toàn bộ database thành JSON file"""
    try:
        db = next(get_db())
        
        # Export users
        users = db.query(User).all()
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "full_name": user.full_name,
                "role": user.role,
                "phone": user.phone,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        # Export payments
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
                "created_at": payment.created_at.isoformat() if payment.created_at else None
            })
        
        # Export handovers
        handovers = db.query(Handover).all()
        handovers_data = []
        for handover in handovers:
            handovers_data.append({
                "id": handover.id,
                "from_person": handover.from_person,
                "to_person": handover.to_person,
                "amount": handover.amount,
                "notes": handover.notes,
                "image_path": handover.image_path,
                "status": handover.status,
                "created_at": handover.created_at.isoformat() if handover.created_at else None
            })
        
        # Create backup
        backup_data = {
            "backup_date": datetime.now().isoformat(),
            "users": users_data,
            "payments": payments_data,
            "handovers": handovers_data
        }
        
        # Save to file
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Database backup saved: {backup_filename}")
        return backup_filename
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def backup_uploads_folder():
    """Backup folder uploads"""
    try:
        backup_folder = f"uploads_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists("uploads"):
            shutil.copytree("uploads", backup_folder)
            print(f"✅ Uploads backup saved: {backup_folder}")
            return backup_folder
        else:
            print("⚠️ No uploads folder found")
            return None
    except Exception as e:
        print(f"❌ Uploads backup failed: {e}")
        return None

def create_full_backup():
    """Tạo backup đầy đủ"""
    print("🔄 Creating full system backup...")
    
    db_backup = backup_database_to_json()
    uploads_backup = backup_uploads_folder()
    
    print("\n📦 Backup Summary:")
    print(f"Database: {db_backup if db_backup else 'FAILED'}")
    print(f"Uploads: {uploads_backup if uploads_backup else 'No files'}")
    print("\n💡 Trước khi deploy:")
    print("1. Chạy script này để backup")
    print("2. Lưu backup files ở nơi an toàn")
    print("3. Deploy lên Railway")
    print("4. Import lại data nếu cần")

if __name__ == "__main__":
    create_full_backup()