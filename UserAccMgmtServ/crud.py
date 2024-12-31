from pymongo.collection import Collection
from fastapi import HTTPException
from models import UserCreate


def create_user(collection: Collection, user_data: dict):
    """
    Create a new user in the database.

    Args:
        collection (Collection): The MongoDB collection to insert the user into.
        user_data (dict): The data for the new user.

    Returns:
        str: The username of the newly created user.

    Raises:
        HTTPException: If an error occurs during user creation.
    """
    try:
        user = UserCreate(**user_data)
        result = collection.insert_one(user.dict(by_alias=True))
        return True
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_user(collection: Collection, username: str):
    """
    Retrieve a user by their username.

    Args:
        collection (Collection): The MongoDB collection to search in.
        username (str): The username of the user to retrieve.

    Returns:
        dict: The retrieved user.

    Raises:
        HTTPException: If the user is not found or if an error occurs during retrieval.
    """
    try:
        user = collection.find_one({"username": username})
        if user:
            user["username"] = str(user["username"])
            return user
        else:
            return False
    except Exception as e:
        return False


def update_user(collection: Collection, username: str, user_data: dict):
    """
    Update an existing user in the database.

    Args:
        collection (Collection): The MongoDB collection to update the user in.
        username (str): The username of the user to update.
        user_data (dict): The updated user data.

    Returns:
        bool: True if the update was successful, False otherwise.

    Raises:
        HTTPException: If the user is not found or if an error occurs during the update.
    """
    try:
        result = collection.update_one({"username": username}, {"$set": user_data})
        if result.modified_count:
            return True
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def delete_user(collection: Collection, username: str):
    """
    Delete a user from the database by their username.

    Args:
        collection (Collection): The MongoDB collection to delete the user from.
        username (str): The username of the user to delete.

    Returns:
        bool: True if the deletion was successful, False otherwise.

    Raises:
        HTTPException: If the user is not found or if an error occurs during deletion.
    """
    try:
        result = collection.delete_one({"username": username})
        if result.deleted_count:
            return True
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
