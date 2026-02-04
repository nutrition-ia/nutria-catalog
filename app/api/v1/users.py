from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.dependencies import get_db
from app.schemas.user import UserProfileCreate, UserProfileResponse
from app.models.user import UserProfile
from datetime import datetime

router = APIRouter()


@router.post("/profiles", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile: UserProfileCreate, db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    Create a new user profile with preferences and restrictions

    This endpoint creates a nutritional profile for a user including:
    - Personal information (name, age, weight, height)
    - Activity level and diet goals
    - Dietary restrictions (vegetarian, vegan, etc.)
    - Food allergies
    - Disliked foods
    - Preferred cuisines

    **Request Body:**
    - `user_id`: UUID of the user (required)
    - `name`: User's name (required)
    - `age`: User's age (required)
    - `weight_kg`: Weight in kg (optional)
    - `height_cm`: Height in cm (optional)
    - `activity_level`: Activity level (optional)
    - `diet_goal`: Diet goal (optional)
    - `dietary_restrictions`: List of dietary restrictions (optional)
    - `allergies`: List of allergies (optional)
    - `disliked_foods`: List of disliked foods (optional)
    - `preferred_cuisines`: List of preferred cuisines (optional)

    **Response:**
    - Returns the created profile with all fields
    """
    try:
        # Check if profile already exists
        existing = db.get(UserProfile, profile.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Perfil já existe para o usuário {profile.user_id}",
            )

        # Create new profile
        db_profile = UserProfile(
            user_id=profile.user_id,
            name=profile.name,
            age=profile.age,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            activity_level=profile.activity_level,
            diet_goal=profile.diet_goal,
            dietary_restrictions=profile.dietary_restrictions or [],
            allergies=profile.allergies or [],
            disliked_foods=profile.disliked_foods or [],
            preferred_cuisines=profile.preferred_cuisines or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

        return db_profile
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar perfil: {str(e)}",
        )


@router.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID, db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    Get a user profile by user_id
    """
    statement = select(UserProfile).where(UserProfile.user_id == user_id)
    profile = db.exec(statement).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Perfil não encontrado para o usuário {user_id}",
        )
    return profile
