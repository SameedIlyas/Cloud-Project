from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class UsageRecord(BaseModel):
    username: str
    date: str  # Changed to str to store ISO format date
    upload_volume_mb: float = Field(default=0, ge=0)
    download_volume_mb: float = Field(default=0, ge=0)
    total_volume_mb: float = Field(default=0, ge=0)
    last_updated: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator("date")
    def validate_date(cls, v):
        """Ensure date is in YYYY-MM-DD format"""
        try:
            if isinstance(v, date):
                return v.isoformat()
            # Try parsing the string to validate format
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")

    @validator("total_volume_mb", pre=True, always=True)
    def calculate_total_volume(cls, v, values):
        """Automatically calculate total volume from upload and download"""
        if "upload_volume_mb" in values and "download_volume_mb" in values:
            return values["upload_volume_mb"] + values["download_volume_mb"]
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BandwidthAlert(BaseModel):
    username: str
    date: str  # Changed to str to store ISO format date
    alert_type: str
    threshold_mb: float = Field(ge=0)
    current_usage_mb: float = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("date")
    def validate_date(cls, v):
        """Ensure date is in YYYY-MM-DD format"""
        try:
            if isinstance(v, date):
                return v.isoformat()
            # Try parsing the string to validate format
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
