import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variable to hold the MongoDB client
mongo_client = None


def get_database():
    global mongo_client
    if mongo_client is None:
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        database_name = os.getenv("DATABASE_NAME")

        if not connection_string or not database_name:
            raise ValueError(
                "Environment variables for MongoDB connection are not set."
            )

        mongo_client = MongoClient(
            connection_string
        )  # Create the MongoDB client only once
        # print("Connected to MongoDB")

    # Return the specific database
    return mongo_client[
        os.getenv("DATABASE_NAME")
    ]  # Use DATABASE_NAME from environment


# Dependency function to be used with FastAPI's dependency injection
def get_db():
    db = get_database()
    try:
        yield db
    finally:
        pass  # No need to close the connection; it's managed by the MongoClient pool


if __name__ == "__main__":
    print(get_database())
