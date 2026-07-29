from fastapi import APIRouter, Depends
from backend.auth import get_current_user
from backend.services.recommendation import recommender

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.get("/personalized")
async def get_personalized(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    # Retrieve hybrid content+collaborative recommendations from engine
    recommendations = await recommender.get_personalized_recommendations(user_id, limit=12)
    return recommendations
