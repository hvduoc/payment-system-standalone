"""
Cloud Storage Setup for Railway Deployment
Sử dụng Cloudinary để lưu trữ files upload an toàn
"""

import os
import cloudinary
import cloudinary.uploader
from typing import Optional

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

def init_cloudinary():
    """Khởi tạo Cloudinary"""
    if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        return True
    return False

def upload_file_to_cloud(file_path: str, folder: str = "payment-receipts") -> Optional[str]:
    """
    Upload file lên Cloudinary
    Returns: URL của file trên cloud
    """
    try:
        if not init_cloudinary():
            print("⚠️ Cloudinary not configured, saving locally")
            return None
            
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type="auto"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"❌ Cloud upload failed: {e}")
        return None

def get_file_storage_path(filename: str, use_cloud: bool = True) -> str:
    """
    Quyết định lưu file ở đâu based on environment
    """
    is_production = bool(os.getenv("DATABASE_URL"))
    
    if is_production and use_cloud:
        return "cloud"  # Signal to use cloud storage
    else:
        return f"uploads/{filename}"  # Local storage