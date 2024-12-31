from fastapi import HTTPException, UploadFile
from pymongo.collection import Collection
from google.cloud import storage
from google.oauth2 import service_account
import os
import mimetypes
import logging
from models import UserStorage
import httpx
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

url = os.getenv("USAGE_MGMT_URL")

# Constants
STORAGE_LIMIT_MB = 50
ALERT_THRESHOLD = 0.8  # 80%
BYTES_PER_MB = 1024 * 1024
MAX_FILE_SIZE_MB = 25  # Maximum size for a single file
ALLOWED_FILE_TYPES = {
    "video": [".mp4", ".mov", ".avi", ".mkv"],
}


class StorageConfig:
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.bucket_name = os.getenv("GCP_BUCKET_NAME")

    def initialize_storage_client(self):
        """Initialize Google Cloud Storage client with credentials"""
        try:
            # If credentials path is provided, use it
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                storage_client = storage.Client(
                    credentials=credentials, project=self.project_id
                )
            else:
                # Fall back to application default credentials
                storage_client = storage.Client()

            # Verify bucket access
            bucket = storage_client.bucket(self.bucket_name)
            bucket.exists()  # This will verify credentials and bucket access

            return storage_client

        except Exception as e:
            raise Exception(f"Failed to initialize storage client: {str(e)}")


class StorageManager:
    def __init__(self):
        storage_config = StorageConfig()
        self.storage_client = storage_config.initialize_storage_client()
        self.bucket = self.storage_client.bucket(storage_config.bucket_name)
        self.logger = logging.getLogger(__name__)

    async def get_user_storage(
        self, collection: Collection, username: str
    ) -> UserStorage:
        """Get or create user storage record"""
        try:
            user_storage = collection.find_one({"username": username})
        except Exception as e:
            pass
        if user_storage is None:
            user_storage = UserStorage(username=username)
            collection.insert_one(user_storage.dict(by_alias=True))
        return UserStorage(**user_storage)

    def validate_file(self, file: UploadFile, file_size_mb: float):
        """Validate file type and size"""
        # Check file size
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE_MB}MB",
            )

        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = [
            ext for types in ALLOWED_FILE_TYPES.values() for ext in types
        ]
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {allowed_extensions}",
            )

        # Validate mime type
        mime_type = mimetypes.guess_type(file.filename)[0]
        if not mime_type:
            raise HTTPException(status_code=400, detail="Could not determine file type")

        return mime_type

    async def can_upload(
        self, collection: Collection, username: str, file_size_mb: float
    ) -> bool:
        """Check if user can upload a file of given size"""
        user_storage = await self.get_user_storage(collection, username)
        return (user_storage.current_usage_mb + file_size_mb) <= STORAGE_LIMIT_MB

    async def should_alert(self, collection: Collection, username: str) -> bool:
        """Check if user should be alerted about storage usage"""
        user_storage = await self.get_user_storage(collection, username)
        return (user_storage.current_usage_mb / STORAGE_LIMIT_MB) >= ALERT_THRESHOLD


# Create storage manager instance
storage_manager = StorageManager()


# In StorageMgmtServ
async def check_bandwidth(
    username: str, file_size_mb: float, operation_type: str, token: str
):
    usage_url = f"{url}/usage/record/"
    headers = {"Authorization": f"{token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            usage_url,
            params={"volume_mb": file_size_mb, "operation_type": operation_type},
            headers=headers,
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Daily bandwidth limit exceeded"
            )
