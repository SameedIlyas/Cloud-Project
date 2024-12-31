from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import Optional
from connection import get_db
from auth import get_current_user
from log import send_log
from pymongo.collection import Collection
import logging
from utils import UsageMonitor, DAILY_BANDWIDTH_LIMIT_MB

# Initialize FastAPI app
app = FastAPI(title="Usage Monitor Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# API Endpoints
@app.post("/usage/record/")
async def record_bandwidth_usage(
    volume_mb: float,
    operation_type: str,
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    username = user.get("username")
    """Record bandwidth usage for a user"""
    try:
        # Validate operation type
        if operation_type not in ["upload", "download"]:
            send_log(username, "UsageMntrServ", "ERROR", "Invalid operation type")
            raise HTTPException(
                status_code=400,
                detail="Invalid operation type. Must be 'upload' or 'download'",
            )

        # Check if can use bandwidth (for uploads)
        if operation_type == "upload":
            if not await UsageMonitor.can_use_bandwidth(
                db.daily_usage, username, volume_mb
            ):
                send_log(
                    username, "UsageMntrServ", "ERROR", "Daily bandwidth limit exceeded"
                )
                raise HTTPException(
                    status_code=400, detail="Daily bandwidth limit exceeded"
                )

        # Record usage
        await UsageMonitor.record_usage(
            db.daily_usage, db.alerts, username, volume_mb, operation_type
        )

        # Get updated usage
        usage = await UsageMonitor.get_daily_usage(db.daily_usage, username)

        send_log(username, "UsageMntrServ", "INFO", "Usage recorded successfully")
        return {
            "message": "Usage recorded successfully",
            "current_usage_mb": usage.total_volume_mb,
            "remaining_mb": DAILY_BANDWIDTH_LIMIT_MB - usage.total_volume_mb,
        }

    except Exception as e:
        send_log(username, "UsageMntrServ", "ERROR", f"Error recording usage: {str(e)}")
        logger.error(f"Error recording usage for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/usage/status/")
async def get_usage_status(
    db: Collection = Depends(get_db), user: dict = Depends(get_current_user)
):
    username = user.get("username")
    """Get current day's usage status for a user"""
    try:
        usage = await UsageMonitor.get_daily_usage(db.daily_usage, username)
        try:
            usage.date = usage.date.isoformat()
        except Exception as e:
            pass
        send_log(
            username, "UsageMntrServ", "INFO", "Usage status retrieved successfully"
        )
        return {
            "username": username,
            "date": usage.date,  # Convert date to string
            "upload_volume_mb": usage.upload_volume_mb,
            "download_volume_mb": usage.download_volume_mb,
            "total_volume_mb": usage.total_volume_mb,
            "daily_limit_mb": DAILY_BANDWIDTH_LIMIT_MB,
            "remaining_mb": DAILY_BANDWIDTH_LIMIT_MB - usage.total_volume_mb,
            "usage_percentage": (usage.total_volume_mb / DAILY_BANDWIDTH_LIMIT_MB)
            * 100,
        }

    except Exception as e:
        send_log(
            username, "UsageMntrServ", "ERROR", f"Error getting usage status: {str(e)}"
        )
        logger.error(f"Error getting usage status for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/usage/alerts/")
async def get_user_alerts(
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
    date: Optional[date] = None,
):
    username = user.get("username")
    """Get bandwidth usage alerts for a user"""
    try:
        query = {"username": username}
        if date:
            try:
                query["date"] = date.isoformat()  # Convert date to string
            except Exception as e:
                query["date"] = date
        alerts_collection = db.alerts
        alerts = (
            await alerts_collection.find(query)
            .sort("timestamp", -1)
            .to_list(length=100)
        )
        send_log(username, "UsageMntrServ", "INFO", "Alerts retrieved successfully")
        return {"alerts": alerts}

    except Exception as e:
        send_log(username, "UsageMntrServ", "ERROR", f"Error getting alerts: {str(e)}")
        logger.error(f"Error getting alerts for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
