from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.user import UserResponse, UserPreferences
from backend.auth import get_current_user
from backend.database import users_collection
from bson import ObjectId

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        preferences=UserPreferences(
            genres=current_user["preferences"].get("genres", []),
            mood=current_user["preferences"].get("mood", ""),
            era=current_user["preferences"].get("era", ""),
            minRating=current_user["preferences"].get("minRating", ""),
            runtime=current_user["preferences"].get("runtime", "")
        )
    )

@router.put("/profile/preferences", response_model=UserResponse)
async def update_preferences(prefs: UserPreferences, current_user: dict = Depends(get_current_user)):
    updated_preferences = {
        "preferences.genres": prefs.genres,
        "preferences.mood": prefs.mood,
        "preferences.era": prefs.era,
        "preferences.minRating": prefs.minRating,
        "preferences.runtime": prefs.runtime
    }

    # Update database
    await users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": updated_preferences}
    )

    # Fetch updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(current_user["id"])})
    
    return UserResponse(
        id=str(updated_user["_id"]),
        username=updated_user["username"],
        email=updated_user["email"],
        preferences=UserPreferences(
            genres=updated_user["preferences"].get("genres", []),
            mood=updated_user["preferences"].get("mood", ""),
            era=updated_user["preferences"].get("era", ""),
            minRating=updated_user["preferences"].get("minRating", ""),
            runtime=updated_user["preferences"].get("runtime", "")
        )
    )
