from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class FileMetadata(BaseModel):
    filename: str
    size_mb: float
    uploaded_at: datetime
    mime_type: str
    file_path: str

    class Config:
        arbitrary_types_allowed = True


class UserStorage(BaseModel):
    username: str
    current_usage_mb: float = 0
    files: List[FileMetadata] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


class StorageStatus(BaseModel):
    username: str
    current_usage_mb: float
    storage_limit_mb: float
    available_space_mb: float
    usage_percentage: float
    should_alert: bool
    files: List[FileMetadata]
