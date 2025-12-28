from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.api.dependencies import get_db
from app.services.food_service import FoodService
from app.schemas.food import (
    FoodSearchRequest,
    FoodSearchResponse,
    FoodSimpleResponse,
)

router = APIRouter()


@router.post("/search", response_model=FoodSearchResponse)
async def search_foods(
    request: FoodSearchRequest,
    db: Session = Depends(get_db)
) -> FoodSearchResponse:
    """
    Search for food items

    This endpoint allows searching for foods using text queries and optional filters.

    **Request Body:**
    - `query`: Search string (required)
    - `limit`: Maximum number of results (default: 10, max: 100)
    - `filters`: Optional filters object
        - `category`: Filter by food category
        - `min_protein`: Minimum protein in grams per 100g
        - `max_calories`: Maximum calories per 100g
        - `source`: Filter by data source (usda, taco, custom)
        - `verified_only`: Only return verified foods (default: false)

    **Response:**
    - `success`: Boolean indicating success
    - `foods`: Array of food objects with basic info and key nutrients
    - `count`: Number of results returned

    **Example Request:**
    ```json
    {
        "query": "chicken breast",
        "limit": 10,
        "filters": {
            "category": "protein",
            "min_protein": 20,
            "max_calories": 200,
            "verified_only": true
        }
    }
    ```
    """
    service = FoodService(db)

    # Search for foods
    foods = service.search_foods(
        query=request.query,
        limit=request.limit,
        filters=request.filters
    )

    # Convert to simple response format with nutrients
    simple_foods = []
    for food in foods:
        food_dict = {
            "id": food.id,
            "name": food.name,
            "category": food.category,
            "serving_size_g": food.serving_size_g,
            "serving_unit": food.serving_unit,
            "calorie_per_100g": food.calorie_per_100g,
            "source": food.source,
            "is_verified": food.is_verified,
        }

        # Add nutrient info if available
        if hasattr(food, 'nutrients') and food.nutrients:
            food_dict["protein_g_100g"] = food.nutrients.protein_g_100g
            food_dict["carbs_g_100g"] = food.nutrients.carbs_g_100g
            food_dict["fat_g_100g"] = food.nutrients.fat_g_100g

        simple_foods.append(FoodSimpleResponse(**food_dict))

    return FoodSearchResponse(
        success=True,
        foods=simple_foods,
        count=len(simple_foods)
    )
