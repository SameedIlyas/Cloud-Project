from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from connection import get_db
from models import LogResponse, LogEntry
from typing import Optional
from auth import get_current_user
from pymongo.collection import Collection
import logging

# App Initialization
app = FastAPI(title="Logging Service")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Routes
@app.post("/log/", response_model=LogResponse)
async def log_entry(entry: LogEntry, db: Collection = Depends(get_db)):
    entry_dict = entry.dict()
    logs_collection = db.logs
    username = entry_dict.get("username")
    try:
        result = logs_collection.insert_one(entry_dict)
        return LogResponse(message="Log entry created successfully")
    except Exception as e:
        logger.error(f"Error creating log entry for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/logs/")
async def get_logs(
    service_name: Optional[str] = None,
    log_level: Optional[str] = None,
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    username = user.get("username")
    query = {}
    if service_name:
        query["service_name"] = service_name
    if log_level:
        query["log_level"] = log_level

    query["username"] = username
    logs_collection = db.logs
    try:
        logs = await logs_collection.find(query).to_list(
            20
        )  # Limit to 20 logs per request
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error retrieving logs for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Custom exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."},
    )
