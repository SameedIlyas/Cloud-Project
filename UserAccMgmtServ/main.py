from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo.collection import Collection
from jose import JWTError, jwt
from connction import get_db
from models import UserCreate, UserLogin, Token
from crud import create_user, get_user, delete_user
from dotenv import load_dotenv
from auth import get_password_hash, verify_password, create_access_token
from log import send_log
import os

# Load environment variables from .env file
load_dotenv()

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# App Initialization
app = FastAPI(title="Login Service")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow access from all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.post("/register/", response_model=dict)
async def register_user(user: UserCreate, db: Collection = Depends(get_db)):
    try:
        existing_user = get_user(db.users, user.username)
        if existing_user:
            send_log(
                user.username, "UserAccMgmtServ", "ERROR", "Username already exists"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        hashed_password = get_password_hash(user.password)
        user_data = {"username": user.username, "password": hashed_password}
        result = create_user(db.users, user_data)
        if not result:
            send_log(user.username, "UserAccMgmtServ", "ERROR", "Error creating user")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating user",
            )
        send_log(
            user.username, "UserAccMgmtServ", "INFO", "User registered successfully"
        )
        return {"message": "User registered successfully"}
    except HTTPException as e:
        send_log(
            user.username,
            "UserAccMgmtServ",
            "ERROR",
            f"Error registering user: {str(e)}",
        )
        raise e
    except Exception as e:
        send_log(
            user.username,
            "UserAccMgmtServ",
            "ERROR",
            f"Unexpected error registering user: {str(e)}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/login/", response_model=Token)
async def login_user(user: UserLogin, db: Collection = Depends(get_db)):
    try:
        existing_user = get_user(db.users, user.username)
        if not existing_user or not verify_password(
            user.password, existing_user["password"]
        ):
            send_log(user.username, "UserAccMgmtServ", "ERROR", "Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        access_token = create_access_token(data={"sub": user.username})
        send_log(
            user.username, "UserAccMgmtServ", "INFO", "User logged in successfully"
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        send_log(
            user.username,
            "UserAccMgmtServ",
            "ERROR",
            f"Error logging in user: {str(e)}",
        )
        raise e
    except Exception as e:
        send_log(
            user.username,
            "UserAccMgmtServ",
            "ERROR",
            f"Unexpected error logging in user: {str(e)}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/verify/", response_model=dict)
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            send_log("Unknown", "UserAccMgmtServ", "ERROR", "Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        send_log(username, "UserAccMgmtServ", "INFO", "Token verified successfully")
        return {"message": "Token is valid", "username": username}
    except JWTError as e:
        send_log("Unknown", "UserAccMgmtServ", "ERROR", f"JWT error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        send_log(
            "Unknown",
            "UserAccMgmtServ",
            "ERROR",
            f"Unexpected error verifying token: {str(e)}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/users/", response_model=dict)
async def delete_user_endpoint(user: UserLogin, db: Collection = Depends(get_db)):
    try:
        existing_user = get_user(db.users, user.username)
        if not existing_user or not verify_password(
            user.password, existing_user["password"]
        ):
            send_log(user.username, "UserAccMgmtServ", "ERROR", "Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        result = delete_user(db.users, existing_user["id"])
        if not result:
            send_log(user.username, "UserAccMgmtServ", "ERROR", "User not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        send_log(user.username, "UserAccMgmtServ", "INFO", "User deleted successfully")
        return {"message": "User deleted successfully"}
    except HTTPException as e:
        send_log(
            user.username, "UserAccMgmtServ", "ERROR", f"Error deleting user: {str(e)}"
        )
        raise e
    except Exception as e:
        send_log(
            user.username,
            "UserAccMgmtServ",
            "ERROR",
            f"Unexpected error deleting user: {str(e)}",
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Custom exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    send_log("Unknown", "UserAccMgmtServ", "ERROR", f"Unhandled error: {str(exc)}")
    return {"message": "An unexpected error occurred. Please try again later."}
