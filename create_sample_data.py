"""
Script tạo dữ liệu mẫu cho hệ thống Building và Payment nâng cấp
"""

from database_production import get_db, Building, User, Payment
from datetime import datetime
import os

def create_sample_buildings():
    """Tạo các tòa nhà mẫu"""
    try:
        db = next(get_db())
        
        # Xóa buildings cũ (nếu có)
        db.query(Building).delete()
        
        buildings = [
            Building(
                name="Landmark 81",
                address="208 Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM",
                description="Tòa nhà cao cấp khu vực Landmark 81",
                is_active=True
            ),
            Building(
                name="Vinhomes Central Park",
                address="Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM", 
                description="Khu căn hộ cao cấp Vinhomes Central Park",
                is_active=True
            ),
            Building(
                name="Saigon Pearl",
                address="92 Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM",
                description="Căn hộ dịch vụ Saigon Pearl",
                is_active=True
            ),
            Building(
                name="The Manor",
                address="91 Nguyễn Hữu Cảnh, Bình Thạnh, TP.HCM",
                description="Tòa nhà The Manor Central Park",
                is_active=True
            ),
            Building(
                name="Diamond Island",
                address="Đảo Kim Cương, Q2, TP.HCM",
                description="Khu biệt thự và căn hộ Diamond Island",
                is_active=True
            )
        ]
        
        for building in buildings:
            db.add(building)
        
        db.commit()
        print("✅ Created sample buildings successfully")
        
        # Hiển thị danh sách buildings
        buildings = db.query(Building).all()
        print("\n📋 Danh sách tòa nhà:")
        for building in buildings:
            print(f"   {building.id}. {building.name} - {building.address}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating buildings: {e}")
        return False

def create_sample_payments():
    """Tạo các payment mẫu"""
    try:
        db = next(get_db())
        
        # Lấy user admin để tạo payments
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("❌ Admin user not found")
            return False
            
        # Lấy buildings
        buildings = db.query(Building).all()
        if not buildings:
            print("❌ No buildings found")
            return False
        
        sample_payments = [
            {
                "booking_id": "BK001",
                "guest_name": "Nguyễn Văn An",
                "room_number": "P1201",
                "building_id": buildings[0].id,
                "amount_due": 2500000,
                "amount_collected": 2500000,
                "payment_method": "bank_transfer",
                "collected_by": "Admin"
            },
            {
                "booking_id": "BK002", 
                "guest_name": "Trần Thị Bình",
                "room_number": "A505",
                "building_id": buildings[1].id,
                "amount_due": 3200000,
                "amount_collected": 3200000,
                "payment_method": "cash",
                "collected_by": "Manager"
            },
            {
                "booking_id": "BK003",
                "guest_name": "Lê Hoàng Châu", 
                "room_number": "B302",
                "building_id": buildings[2].id,
                "amount_due": 1800000,
                "amount_collected": 1800000,
                "payment_method": "momo",
                "collected_by": "Admin"
            },
            {
                "booking_id": "BK004",
                "guest_name": "Phạm Minh Đức",
                "room_number": "C108",
                "building_id": buildings[3].id,
                "amount_due": 4500000,
                "amount_collected": 4200000,
                "payment_method": "credit_card",
                "collected_by": "Assistant"
            },
            {
                "booking_id": "BK005",
                "guest_name": "Võ Thị Emy",
                "room_number": "D701",
                "building_id": buildings[4].id,
                "amount_due": 2800000,
                "amount_collected": 2800000,
                "payment_method": "zalopay",
                "collected_by": "Manager"
            }
        ]
        
        for payment_data in sample_payments:
            payment = Payment(
                booking_id=payment_data["booking_id"],
                guest_name=payment_data["guest_name"],
                room_number=payment_data["room_number"],
                building_id=payment_data["building_id"],
                amount_due=payment_data["amount_due"],
                amount_collected=payment_data["amount_collected"],
                payment_method=payment_data["payment_method"],
                collected_by=payment_data["collected_by"],
                notes=f"Payment sample for {payment_data['guest_name']}",
                status="completed",
                added_by_user_id=admin_user.id
            )
            db.add(payment)
        
        db.commit()
        print("✅ Created sample payments successfully")
        
        # Hiển thị payments
        payments = db.query(Payment).all()
        print(f"\n💰 Tạo {len(payments)} payments mẫu")
        for payment in payments:
            building = db.query(Building).filter(Building.id == payment.building_id).first()
            print(f"   {payment.booking_id}: {payment.guest_name} - {building.name if building else 'N/A'} - {payment.room_number}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating payments: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Creating sample data for enhanced payment system...")
    
    # Check environment
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("🚀 Using PostgreSQL (Production)")
    else:
        print("💻 Using SQLite (Development)")
    
    # Create buildings first
    if create_sample_buildings():
        # Then create payments
        create_sample_payments()
        
    print("\n🎉 Sample data creation completed!")
    print("👆 Bạn có thể test các tính năng:")
    print("   - Xem payments theo tòa nhà")
    print("   - Edit/Delete payments") 
    print("   - Quản lý tòa nhà")
    print("   - Filter và export data")