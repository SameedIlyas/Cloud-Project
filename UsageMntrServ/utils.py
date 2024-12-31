from pymongo.collection import Collection
from datetime import datetime, date
from models import UsageRecord, BandwidthAlert
import logging

# Constants
DAILY_BANDWIDTH_LIMIT_MB = 100
BYTES_PER_MB = 1024 * 1024

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UsageMonitor:
    @staticmethod
    async def get_daily_usage(
        usage_collection: Collection, username: str, current_date: date = None
    ) -> UsageRecord:
        """Get or create daily usage record for user"""
        if current_date is None:
            current_date = date.today()

        usage = usage_collection.find_one(
            {"username": username, "date": current_date.isoformat()}
        )

        if not usage:
            usage = UsageRecord(
                username=username,
                date=current_date.isoformat(),
                last_updated=datetime.utcnow(),
            ).dict()
            usage_collection.insert_one(usage)

        return UsageRecord(**usage)

    @staticmethod
    async def can_use_bandwidth(
        usage_collection: Collection, username: str, required_mb: float
    ) -> bool:
        """Check if user has enough bandwidth remaining for the day"""
        usage = await UsageMonitor.get_daily_usage(usage_collection, username)
        return (usage.total_volume_mb + required_mb) <= DAILY_BANDWIDTH_LIMIT_MB

    @staticmethod
    async def record_usage(
        usage_collection: Collection,
        alert_collection: Collection,
        username: str,
        volume_mb: float,
        operation_type: str,
    ):
        """Record bandwidth usage for upload/download operations"""
        current_date = date.today()

        # Update fields based on operation type
        update_field = (
            "upload_volume_mb" if operation_type == "upload" else "download_volume_mb"
        )

        # Update usage record
        result = usage_collection.update_one(
            {"username": username, "date": current_date.isoformat()},
            {
                "$inc": {update_field: volume_mb, "total_volume_mb": volume_mb},
                "$set": {"last_updated": datetime.utcnow()},
            },
            upsert=True,
        )

        # Check if need to create alert
        usage = await UsageMonitor.get_daily_usage(usage_collection, username)
        if usage.total_volume_mb >= DAILY_BANDWIDTH_LIMIT_MB:
            await UsageMonitor.create_alert(
                alert_collection,
                username,
                "LIMIT_EXCEEDED",
                DAILY_BANDWIDTH_LIMIT_MB,
                usage.total_volume_mb,
            )
        elif usage.total_volume_mb >= (DAILY_BANDWIDTH_LIMIT_MB * 0.8):  # 80% threshold
            await UsageMonitor.create_alert(
                alert_collection,
                username,
                "APPROACHING_LIMIT",
                DAILY_BANDWIDTH_LIMIT_MB,
                usage.total_volume_mb,
            )

    @staticmethod
    async def create_alert(
        alert_collection: Collection,
        username: str,
        alert_type: str,
        threshold_mb: float,
        current_usage_mb: float,
    ):
        """Create bandwidth usage alert"""
        alert = BandwidthAlert(
            username=username,
            date=date.today().isoformat(),  # Convert date to datetime
            alert_type=alert_type,
            threshold_mb=threshold_mb,
            current_usage_mb=current_usage_mb,
            timestamp=datetime.utcnow(),
        )

        alert_collection.insert_one(alert.dict())
        logger.info(f"Created {alert_type} alert for user {username}")
