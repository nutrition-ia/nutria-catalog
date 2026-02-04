from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.dependencies import get_db
from app.models.user import UserProfile
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedFoodItem,
    UserFiltersResponse,
)
from app.services import recomendation_service

router = APIRouter()


def _get_user_profile(db: Session, user_id: UUID) -> UserProfile:
    """Get user profile or raise 404"""
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile with ID {user_id} not found",
        )
    return profile


@router.post("/", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest, db: Session = Depends(get_db)
) -> RecommendationResponse:
    """
    Get personalized food recommendations for a user.

    This endpoint returns foods that are safe and suitable for the user based on:
    - **Dietary restrictions** (vegetarian, vegan, gluten-free, etc.)
    - **Allergies** (peanuts, lactose, gluten, etc.)
    - **Disliked foods** (foods the user doesn't want to see)

    **Request Body:**
    - `user_id`: UUID of the user profile (required)
    - `limit`: Maximum number of recommendations (default: 10, max: 100)
      - **Note for AI agents**: Keep limit ≤20 for small context models (e.g., gpt-4.1-mini with 8k tokens)
    - `category`: Optional category filter (e.g., "protein", "vegetable")

    **Response:**
    - `success`: Boolean indicating success
    - `foods`: Array of recommended food items
    - `count`: Number of recommendations returned
    - `filters_applied`: Summary of user restrictions applied

    **Example Request:**
    ```json
    {
        "user_id": "uuid-here",
        "limit": 20,
        "category": "protein"
    }
    ```
    """
    profile = _get_user_profile(db, request.user_id)

    if request.category:
        foods = recomendation_service.get_foods_by_category(
            session=db, profile=profile, category=request.category, limit=request.limit
        )
    else:
        foods = recomendation_service.recommend_foods(
            session=db, profile=profile, limit=request.limit
        )

    recommended_items = []
    for food in foods:
        item_dict = {
            "id": food.id,
            "name": food.name,
            "category": food.category,
            "serving_size_g": food.serving_size_g,
            "serving_unit": food.serving_unit,
            "calorie_per_100g": food.calorie_per_100g,
            "source": food.source,
            "is_verified": food.is_verified,
        }

        if hasattr(food, "nutrients") and food.nutrients:
            item_dict["protein_g_100g"] = food.nutrients.protein_g_100g
            item_dict["carbs_g_100g"] = food.nutrients.carbs_g_100g
            item_dict["fat_g_100g"] = food.nutrients.fat_g_100g

        recommended_items.append(RecommendedFoodItem(**item_dict))

    filters_applied = {
        "dietary_restrictions": profile.dietary_restrictions or [],
        "allergies": profile.allergies or [],
        "disliked_foods": profile.disliked_foods or [],
    }

    return RecommendationResponse(
        success=True,
        foods=recommended_items,
        count=len(recommended_items),
        filters_applied=filters_applied,
    )


@router.get("/{user_id}/filters", response_model=UserFiltersResponse)
async def get_user_filters(
    user_id: UUID, db: Session = Depends(get_db)
) -> UserFiltersResponse:
    """
    Get the dietary filters for a specific user.

    This endpoint returns the user's dietary restrictions, allergies,
    and disliked foods that are used to filter recommendations.

    **Path Parameters:**
    - `user_id`: UUID of the user profile

    **Response:**
    - `user_id`: The user's UUID
    - `dietary_restrictions`: List of dietary restrictions
    - `allergies`: List of allergies
    - `disliked_foods`: List of disliked foods
    """
    profile = _get_user_profile(db, user_id)

    return UserFiltersResponse(
        user_id=user_id,
        dietary_restrictions=profile.dietary_restrictions or [],
        allergies=profile.allergies or [],
        disliked_foods=profile.disliked_foods or [],
    )
