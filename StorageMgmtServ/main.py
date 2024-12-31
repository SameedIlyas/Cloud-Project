from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pymongo.collection import Collection
from datetime import datetime
from connection import get_db
from auth import get_current_user
from log import send_log
from fastapi.responses import StreamingResponse
from io import BytesIO
from models import FileMetadata, StorageStatus
from utils import storage_manager, BYTES_PER_MB, STORAGE_LIMIT_MB, check_bandwidth


# Initialize FastAPI app
app = FastAPI(title="Storage Management Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/storage/status/", response_model=StorageStatus)
async def get_storage_status(
    db: Collection = Depends(get_db), user: dict = Depends(get_current_user)
):
    username = user.get("username")
    """Get storage status for a user"""
    try:
        user_storage = await storage_manager.get_user_storage(db.userstorage, username)
        should_alert = await storage_manager.should_alert(db.userstorage, username)

        send_log(
            username, "StorageMgmtServ", "INFO", "Storage status retrieved successfully"
        )
        return StorageStatus(
            username=username,
            current_usage_mb=user_storage.current_usage_mb,
            storage_limit_mb=STORAGE_LIMIT_MB,
            available_space_mb=STORAGE_LIMIT_MB - user_storage.current_usage_mb,
            usage_percentage=(user_storage.current_usage_mb / STORAGE_LIMIT_MB) * 100,
            should_alert=should_alert,
            files=user_storage.files,
        )
    except Exception as e:
        send_log(
            username,
            "StorageMgmtServ",
            "ERROR",
            f"Error getting storage status: {str(e)}",
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/storage/upload/")
async def upload_file(
    file: UploadFile = File(...),
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    username = user.get("username")  # Get username from token
    """Upload a file to user's storage"""
    try:
        # Read file into memory to get size
        contents = await file.read()
        file_size_mb = len(contents) / BYTES_PER_MB

        # Validate file
        mime_type = storage_manager.validate_file(file, file_size_mb)

        await check_bandwidth(
            username, file_size_mb, operation_type="upload", token=authorization
        )
        # Check if user can upload
        if not await storage_manager.can_upload(db.userstorage, username, file_size_mb):
            send_log(username, "StorageMgmtServ", "ERROR", "Storage limit exceeded")
            raise HTTPException(
                status_code=400,
                detail="Storage limit exceeded. Please free up space before uploading.",
            )

        # Upload to Google Cloud Storage
        blob_name = f"users/{username}/{datetime.utcnow().timestamp()}_{file.filename}"
        blob = storage_manager.bucket.blob(blob_name)
        blob.upload_from_string(contents, content_type=mime_type)

        # Update MongoDB
        file_metadata = FileMetadata(
            filename=file.filename,
            size_mb=file_size_mb,
            uploaded_at=datetime.utcnow(),
            mime_type=mime_type,
            file_path=blob_name,
        )
        collection = db.userstorage
        collection.update_one(
            {"username": username},
            {
                "$push": {"files": file_metadata.dict()},
                "$inc": {"current_usage_mb": file_size_mb},
                "$set": {"last_updated": datetime.utcnow()},
            },
        )

        should_alert = await storage_manager.should_alert(db.userstorage, username)
        send_log(username, "StorageMgmtServ", "INFO", "File uploaded successfully")
        return {
            "message": "File uploaded successfully",
            "should_alert": should_alert,
            "file_metadata": file_metadata,
        }

    except Exception as e:
        send_log(username, "StorageMgmtServ", "ERROR", f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/storage/files/{filename}")
async def delete_file(
    filename: str,
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    username = user.get("username")
    """Delete a file from user's storage"""
    try:
        # Get user storage record
        user_storage = await storage_manager.get_user_storage(db.userstorage, username)

        # Find file metadata
        file_to_delete = None
        for file in user_storage.files:
            if file.filename == filename:
                file_to_delete = file
                break

        if not file_to_delete:
            send_log(username, "StorageMgmtServ", "ERROR", "File not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from Google Cloud Storage
        blob = storage_manager.bucket.blob(file_to_delete.file_path)
        if blob.exists():
            blob.delete()

        # Update MongoDB
        collection = db.userstorage
        result = collection.update_one(
            {"username": username},
            {
                "$pull": {"files": {"filename": filename}},
                "$inc": {"current_usage_mb": -file_to_delete.size_mb},
                "$set": {"last_updated": datetime.utcnow()},
            },
        )

        send_log(username, "StorageMgmtServ", "INFO", "File deleted successfully")
        return {"message": "File deleted successfully"}

    except Exception as e:
        send_log(username, "StorageMgmtServ", "ERROR", f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/files/")
async def list_files(
    db: Collection = Depends(get_db), user: dict = Depends(get_current_user)
):
    username = user.get("username")
    """List all files in user's storage"""
    try:
        user_storage = await storage_manager.get_user_storage(db.userstorage, username)
        send_log(username, "StorageMgmtServ", "INFO", "Files listed successfully")
        return {"files": user_storage.files}
    except Exception as e:
        send_log(username, "StorageMgmtServ", "ERROR", f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handling for common exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    send_log("Unknown", "StorageMgmtServ", "ERROR", f"Unhandled error: {str(exc)}")
    return {
        "status_code": 500,
        "detail": "An unexpected error occurred. Please try again later.",
    }


@app.get("/storage/download/{filename}")
async def download_file(
    filename: str,
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    """Download a file from user's storage"""
    username = user.get("username")
    try:
        # Get user storage record
        user_storage = await storage_manager.get_user_storage(db.userstorage, username)

        # Find file metadata
        file_to_download = None
        for file in user_storage.files:
            if file.filename == filename:
                file_to_download = file
                break

        if not file_to_download:
            send_log(username, "StorageMgmtServ", "ERROR", "File not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Get the file from Google Cloud Storage
        blob = storage_manager.bucket.blob(file_to_download.file_path)
        if not blob.exists():
            send_log(username, "StorageMgmtServ", "ERROR", "File not found in storage")
            raise HTTPException(status_code=404, detail="File not found in storage")

        # Check bandwidth allowance
        await check_bandwidth(
            username,
            file_to_download.size_mb,
            operation_type="download",
            token=authorization,
        )

        # Download file to memory
        file_content = BytesIO()
        blob.download_to_file(file_content)
        file_content.seek(0)

        # Create response headers
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": file_to_download.mime_type,
        }

        send_log(username, "StorageMgmtServ", "INFO", "File downloaded successfully")
        return StreamingResponse(
            file_content, headers=headers, media_type=file_to_download.mime_type
        )

    except Exception as e:
        send_log(username, "StorageMgmtServ", "ERROR", f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/storage/stream/{filename}")
async def stream_video(
    filename: str,
    db: Collection = Depends(get_db),
    user: dict = Depends(get_current_user),
    authorization: str = Header(None),
):
    """Stream a video file from user's storage"""
    username = user.get("username")
    try:
        # Get user storage record
        user_storage = await storage_manager.get_user_storage(db.userstorage, username)

        # Find file metadata
        file_to_stream = None
        for file in user_storage.files:
            if file.filename == filename:
                file_to_stream = file
                break

        if not file_to_stream:
            send_log(username, "StorageMgmtServ", "ERROR", "File not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Get the file from Google Cloud Storage
        blob = storage_manager.bucket.blob(file_to_stream.file_path)
        if not blob.exists():
            send_log(username, "StorageMgmtServ", "ERROR", "File not found in storage")
            raise HTTPException(status_code=404, detail="File not found in storage")

        # Check bandwidth allowance
        await check_bandwidth(
            username,
            file_to_stream.size_mb,
            # operation_type="stream",
            operation_type="download",
            token=authorization,
        )

        # Stream the file
        def iterfile():
            with blob.open("rb") as f:
                yield from f

        send_log(username, "StorageMgmtServ", "INFO", "File streamed successfully")
        return StreamingResponse(iterfile(), media_type=file_to_stream.mime_type)

    except Exception as e:
        send_log(username, "StorageMgmtServ", "ERROR", f"Stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



