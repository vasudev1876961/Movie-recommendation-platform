from fastapi import APIRouter, HTTPException, status
from backend.models.user import UserCreate, UserLogin, Token, UserResponse, UserPreferences
from backend.database import users_collection
from backend.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate):
    # Check if username exists
    existing_username = await users_collection.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = await users_collection.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and store user
    hashed_pass = hash_password(user_data.password)
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_pass,
        "preferences": {
            "genres": [],
            "mood": "",
            "era": "",
            "minRating": "",
            "runtime": ""
        }
      }
      
    result = await users_collection.insert_one(user_dict)
    
    # Generate Token
    access_token = create_access_token(data={"sub": user_data.username})
    
    user_res = UserResponse(
        id=str(result.inserted_id),
        username=user_data.username,
        email=user_data.email,
        preferences=UserPreferences()
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_res
    )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await users_collection.find_one({"username": credentials.username})
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
        
    access_token = create_access_token(data={"sub": user["username"]})
    
    user_res = UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        preferences=UserPreferences(
            genres=user["preferences"].get("genres", []),
            mood=user["preferences"].get("mood", ""),
            era=user["preferences"].get("era", ""),
            minRating=user["preferences"].get("minRating", ""),
            runtime=user["preferences"].get("runtime", "")
        )
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_res
    )
