"""
Google Drive Auto Backup Integration
Tự động backup dữ liệu lên Google Drive 2TB miễn phí
"""

import os
import json
import schedule
import time
import uuid
import io
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import pickle
import io
import requests

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveBackup:
    def __init__(self):
        self.service = None
        self.backup_folder_id = None
        self.creds = None
        
    def authenticate(self):
        """Authenticate với Google Drive API"""
        creds = None
        # Token file để lưu credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # Nếu không có credentials hợp lệ, tạo mới
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Cần tạo credentials.json từ Google Cloud Console
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Lưu credentials cho lần sau
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.creds = creds
        self.service = build('drive', 'v3', credentials=creds)
        print("Google Drive authentication successful")
        return self.service
    
    def create_backup_folder(self):
        """Tạo folder backup trên Google Drive"""
        try:
            # Tìm folder backup hiện có
            query = "name='Airbnb_Payment_Backups' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                self.backup_folder_id = items[0]['id']
                print(f"✅ Found existing backup folder: {self.backup_folder_id}")
            else:
                # Tạo folder mới
                folder_metadata = {
                    'name': 'Airbnb_Payment_Backups',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                self.backup_folder_id = folder.get('id')
                print(f"✅ Created new backup folder: {self.backup_folder_id}")
                
        except Exception as e:
            print(f"❌ Error creating backup folder: {e}")
            
    def backup_to_drive(self, backup_data, filename=None):
        """Upload backup data to Google Drive"""
        temp_file = None
        try:
            if not filename:
                filename = f"airbnb_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Tạo file tạm thời với unique name để tránh conflict
            temp_file = f"temp_{uuid.uuid4().hex[:8]}_{filename}"
            
            # Đảm bảo file được close hoàn toàn trước khi upload
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # Upload lên Google Drive
            file_metadata = {
                'name': filename,
                'parents': [self.backup_folder_id] if self.backup_folder_id else []
            }
            
            media = MediaFileUpload(temp_file, mimetype='application/json')
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime'
            ).execute()
            
            print(f"✅ Backup uploaded: {file['name']} ({file['size']} bytes)")
            return file
            
        except Exception as e:
            print(f"❌ Error uploading backup: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Đảm bảo xóa file tạm thời trong mọi trường hợp
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"🗑️ Cleaned up temp file: {temp_file}")
                except Exception as e:
                    print(f"⚠️ Could not remove temp file {temp_file}: {e}")
    
    def backup_image_to_drive(self, local_image_path, drive_filename=None):
        """Upload handover image to Google Drive"""
        try:
            if not os.path.exists(local_image_path):
                print(f"⚠️ Image file not found: {local_image_path}")
                return None
                
            if not drive_filename:
                drive_filename = os.path.basename(local_image_path)
            
            # Create images subfolder if not exists
            images_folder_id = self.get_or_create_images_folder()
            
            file_metadata = {
                'name': drive_filename,
                'parents': [images_folder_id] if images_folder_id else []
            }
            
            # Detect mime type
            if local_image_path.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif local_image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'  # default
            
            media = MediaFileUpload(local_image_path, mimetype=mime_type)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,webContentLink'
            ).execute()
            
            # Make file viewable by anyone with link for restore purposes
            try:
                permission = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                self.service.permissions().create(
                    fileId=file['id'],
                    body=permission
                ).execute()
                print(f"✅ Made image publicly accessible")
            except Exception as perm_error:
                print(f"⚠️ Permission warning: {perm_error}")
            
            print(f"✅ Image uploaded: {file['name']} ({file['size']} bytes)")
            print(f"🔗 View: {file.get('webViewLink')}")
            return file
            
        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            return None
    
    def get_or_create_images_folder(self):
        """Get or create images subfolder in backup folder"""
        try:
            if not self.backup_folder_id:
                return None
                
            # Check if images folder exists
            query = f"'{self.backup_folder_id}' in parents and name='handover_images' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id,name)").execute()
            
            if results.get('files'):
                folder_id = results['files'][0]['id']
                print(f"✅ Found existing images folder: {folder_id}")
                return folder_id
            else:
                # Create new images folder
                folder_metadata = {
                    'name': 'handover_images',
                    'parents': [self.backup_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')
                print(f"✅ Created new images folder: {folder_id}")
                return folder_id
                
        except Exception as e:
            print(f"❌ Error with images folder: {e}")
            return None
            
    def list_backups(self, limit=10):
        """List backup files trên Google Drive"""
        try:
            query = f"'{self.backup_folder_id}' in parents and trashed=false" if self.backup_folder_id else "name contains 'airbnb_backup' and trashed=false"
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=limit,
                fields="files(id,name,size,createdTime,modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
            return []
            
    def get_backup_content(self, file_id):
        """Get backup file content as JSON"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            return json.loads(content.decode('utf-8'))
        except Exception as e:
            print(f"❌ Error getting backup content: {e}")
            return None

    def download_image_from_drive(self, file_id, local_path):
        """Download image from Google Drive to local path"""
        try:
            # Ensure uploads directory exists
            uploads_dir = os.path.dirname(local_path)
            if uploads_dir and not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir, exist_ok=True)
                print(f"📁 Created directory: {uploads_dir}")
            
            # Get file info first
            file_info = self.service.files().get(fileId=file_id, fields='name,size,mimeType').execute()
            print(f"📥 Downloading: {file_info.get('name')} ({file_info.get('size')} bytes)")
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            
            # Save to local file
            with open(local_path, 'wb') as f:
                f.write(content)
            
            # Verify file was saved
            if os.path.exists(local_path):
                local_size = os.path.getsize(local_path)
                print(f"✅ Downloaded image: {local_path} ({local_size} bytes)")
                return True
            else:
                print(f"❌ File not created: {local_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading image {file_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def restore_from_backup(self, file_id, restore_images=True):
        """Complete restore from backup including images"""
        try:
            # Get backup content
            backup_data = self.get_backup_content(file_id)
            if not backup_data:
                return {"success": False, "error": "Could not read backup file"}
            
            restored_counts = {
                "payments": 0,
                "handovers": 0,
                "buildings": 0,
                "users": 0,
                "images": 0
            }
            
            # Restore images if requested
            if restore_images and "handovers" in backup_data:
                for handover in backup_data["handovers"]:
                    if "drive_image_id" in handover and handover["drive_image_id"]:
                        # Generate local path
                        if handover.get("image_path"):
                            local_path = handover["image_path"]
                            if not local_path.startswith("uploads/"):
                                local_path = f"uploads/{os.path.basename(local_path)}"
                            
                            success = self.download_image_from_drive(
                                handover["drive_image_id"], 
                                local_path
                            )
                            if success:
                                restored_counts["images"] += 1
                                # Update handover image_path to local path
                                handover["image_path"] = local_path
            
            return {
                "success": True,
                "backup_data": backup_data,
                "restored_counts": restored_counts
            }
            
        except Exception as e:
            print(f"❌ Error restoring from backup: {e}")
            return {"success": False, "error": str(e)}
            
    def download_backup(self, file_id, local_filename):
        """Download backup từ Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                
            fh.seek(0)
            with open(local_filename, 'wb') as f:
                f.write(fh.read())
                
            print(f"✅ Backup downloaded: {local_filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading backup: {e}")
            return False
            
    def cleanup_old_backups(self, keep_days=30):
        """Xóa backup files cũ hơn keep_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            backups = self.list_backups(limit=100)
            
            deleted_count = 0
            for backup in backups:
                created_time = datetime.fromisoformat(backup['createdTime'].replace('Z', '+00:00'))
                if created_time < cutoff_date:
                    self.service.files().delete(fileId=backup['id']).execute()
                    print(f"🗑️ Deleted old backup: {backup['name']}")
                    deleted_count += 1
                    
            print(f"✅ Cleaned up {deleted_count} old backups")
            
        except Exception as e:
            print(f"❌ Error cleaning up backups: {e}")

def get_system_backup():
    """Lấy backup data từ Railway API"""
    try:
        # URL Railway app
        railway_url = os.getenv('RAILWAY_URL', 'https://payment-system-standalone-production.up.railway.app')
        
        response = requests.post(f"{railway_url}/api/backup/create")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get backup from Railway: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting system backup: {e}")
        return None

def daily_backup_job():
    """Daily backup job"""
    print(f"🚀 Starting daily backup job at {datetime.now()}")
    
    # Initialize Google Drive backup
    drive_backup = GoogleDriveBackup()
    drive_backup.authenticate()
    drive_backup.create_backup_folder()
    
    # Get system backup
    backup_data = get_system_backup()
    if backup_data:
        # Upload to Google Drive
        result = drive_backup.backup_to_drive(backup_data)
        if result:
            print("✅ Daily backup completed successfully")
            
            # Cleanup old backups
            drive_backup.cleanup_old_backups(keep_days=30)
        else:
            print("❌ Daily backup failed")
    else:
        print("❌ Could not get backup data")

def setup_backup_schedule():
    """Setup backup schedule"""
    # Daily backup at 2:00 AM Vietnam time
    schedule.every().day.at("02:00").do(daily_backup_job)
    
    # Weekly full backup (Sundays at 3:00 AM)
    schedule.every().sunday.at("03:00").do(lambda: daily_backup_job())
    
    print("📅 Backup schedule configured:")
    print("   - Daily backup: 2:00 AM")
    print("   - Weekly backup: Sunday 3:00 AM")
    print("   - Retention: 30 days")

def run_backup_service():
    """Run backup service"""
    print("🔄 Starting Google Drive Backup Service...")
    setup_backup_schedule()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    # Test manual backup
    print("🧪 Testing Google Drive backup...")
    
    drive_backup = GoogleDriveBackup()
    
    try:
        drive_backup.authenticate()
        drive_backup.create_backup_folder()
        
        # Test backup
        test_data = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Test backup from Python script"
        }
        
        result = drive_backup.backup_to_drive(test_data, "test_backup.json")
        if result:
            print("✅ Test backup successful!")
            
            # List backups
            backups = drive_backup.list_backups(5)
            print("\n📁 Recent backups:")
            for backup in backups:
                print(f"   - {backup['name']} ({backup['size']} bytes)")
                
        else:
            print("❌ Test backup failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Manual setup required:")
        print("1. Go to https://console.developers.google.com/")
        print("2. Create new project or select existing")
        print("3. Enable Google Drive API")
        print("4. Create credentials (OAuth 2.0)")
        print("5. Download credentials.json to this folder")
        print("6. Run script again")