from fastapi import APIRouter, Depends, HTTPException, status
from backend.auth import get_current_user
from backend.database import watchlist_collection
from backend.routers.movies import get_details

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])

@router.get("")
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    user_watchlist = await watchlist_collection.find_one({"user_id": current_user["id"]})
    if user_watchlist:
        return user_watchlist.get("movies", [])
    return []

@router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(movie_id: int, current_user: dict = Depends(get_current_user)):
    # 1. Fetch movie details to ensure we store a complete movie record
    try:
        movie = await get_details(movie_id)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie details could not be resolved to bookmark"
        )
        
    # Simplify properties to save database storage
    simple_movie = {
        "id": movie["id"],
        "title": movie["title"],
        "year": movie["year"],
        "rating": movie["rating"],
        "genres": movie["genres"],
        "poster": movie["poster"],
        "backdrop": movie["backdrop"],
        "runtime": movie["runtime"]
    }
    
    # 2. Check if user already has a watchlist document
    user_watchlist = await watchlist_collection.find_one({"user_id": current_user["id"]})
    
    if not user_watchlist:
        # Create watchlist document
        await watchlist_collection.insert_one({
            "user_id": current_user["id"],
            "movies": [simple_movie]
        })
    else:
        # Check if movie already exists in list
        movies = user_watchlist.get("movies", [])
        if not any(m["id"] == movie_id for m in movies):
            await watchlist_collection.update_one(
                {"user_id": current_user["id"]},
                {"$push": {"movies": simple_movie}}
            )
            
    return {"message": "Movie added to watchlist successfully"}

@router.delete("/{movie_id}")
async def remove_from_watchlist(movie_id: int, current_user: dict = Depends(get_current_user)):
    user_watchlist = await watchlist_collection.find_one({"user_id": current_user["id"]})
    if not user_watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )
        
    await watchlist_collection.update_one(
        {"user_id": current_user["id"]},
        {"$pull": {"movies": {"id": movie_id}}}
      )
      
    return {"message": "Movie removed from watchlist successfully"}
