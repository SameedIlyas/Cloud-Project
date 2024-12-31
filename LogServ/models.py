from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Log(BaseModel):
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    service_name: str
    log_level: str  # e.g., "INFO", "ERROR", "DEBUG"
    message: str


class LogEntry(Log):
    username: str


class LogResponse(BaseModel):
    message: str
