from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.services.search_service import SearchService
from app.api.dependencies import get_db
from app.services.food_service import FoodService
from app.schemas.food import (
    FoodSearchRequest,
    FoodSearchResponse,
    FoodSimpleResponse,
    SimilarFoodRequest,
    SimilarFoodItem,
    SimilarFoodsResponse,
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

async def semantic_search(
        request: FoodSearchRequest,
        db: Session = Depends(get_db),
        ) -> FoodSearchResponse:
        """
        Busca semântica de alimentos usando embeddings vetoriais

        Mais inteligente que busca textual - entende contexto e sinônimos.
        Exemplo: "comida rica em proteína para ganho muscular"
        encontrará carnes, ovos, etc.
        """

        service = SearchService(db)

        foods = service.hybrid_search(
            query=request.query,
            limit=request.limit,
            filters=request.filters
        )

        simple_foods = [
            FoodSimpleResponse(
                id=food.id,
                name=food.name,
                category=food.category,
                serving_size_g=food.serving_size_g,
                serving_unit=food.serving_unit,
                calorie_per_100g=food.calorie_per_100g,
                source=food.source,
                is_verified=food.is_verified,
                protein_g_100g=getattr(food.nutrients, 'protein_g_100g', None),
                carbs_g_100g=getattr(food.nutrients, 'carbs_g_100g', None),
                fat_g_100g=getattr(food.nutrients, 'fat_g_100g', None),
            )
            for food in foods
        ]

        return FoodSearchResponse(
            success=True,
            foods=simple_foods,
            count=len(simple_foods)
        )


@router.post("/similar", response_model=SimilarFoodsResponse)
async def find_similar_foods(
    request: SimilarFoodRequest,
    db: Session = Depends(get_db)
) -> SimilarFoodsResponse:
    """
    Find foods with similar nutritional profile to substitute in a diet.

    This endpoint finds foods that have similar macronutrient profiles,
    useful for finding alternatives or substitutes in meal planning.

    **Request Body:**
    - `food_id`: UUID of the reference food (required)
    - `limit`: Maximum number of similar foods to return (default: 10, max: 50)
    - `same_category`: Only return foods from the same category (default: false)
    - `tolerance`: Nutritional similarity tolerance (0.3 = 30% difference allowed)

    **Response:**
    - `success`: Boolean indicating success
    - `reference_food`: The original food being compared
    - `similar_foods`: Array of similar foods with similarity scores
    - `count`: Number of similar foods found

    **Similarity Calculation:**
    Uses weighted comparison of macronutrients:
    - Calories: 30%
    - Protein: 25%
    - Carbs: 20%
    - Fat: 15%
    - Fiber: 10%

    **Example Request:**
    ```json
    {
        "food_id": "uuid-here",
        "limit": 10,
        "same_category": false,
        "tolerance": 0.3
    }
    ```
    """
    service = FoodService(db)

    # Get reference food
    ref_food = service.get_food_with_nutrients(request.food_id)
    if not ref_food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food with ID {request.food_id} not found"
        )

    # Find similar foods
    similar_results = service.find_similar_foods(
        food_id=request.food_id,
        limit=request.limit,
        same_category=request.same_category,
        tolerance=request.tolerance
    )

    # Build reference food response
    ref_nutrients = ref_food.nutrients if hasattr(ref_food, 'nutrients') else None
    reference_response = FoodSimpleResponse(
        id=ref_food.id,
        name=ref_food.name,
        category=ref_food.category,
        serving_size_g=ref_food.serving_size_g,
        serving_unit=ref_food.serving_unit,
        calorie_per_100g=ref_food.calorie_per_100g,
        source=ref_food.source,
        is_verified=ref_food.is_verified,
        protein_g_100g=ref_nutrients.protein_g_100g if ref_nutrients else None,
        carbs_g_100g=ref_nutrients.carbs_g_100g if ref_nutrients else None,
        fat_g_100g=ref_nutrients.fat_g_100g if ref_nutrients else None,
    )

    # Build similar foods response
    similar_foods = []
    for food, nutrients, score in similar_results:
        similar_foods.append(SimilarFoodItem(
            id=food.id,
            name=food.name,
            category=food.category,
            calorie_per_100g=food.calorie_per_100g,
            protein_g_100g=nutrients.protein_g_100g,
            carbs_g_100g=nutrients.carbs_g_100g,
            fat_g_100g=nutrients.fat_g_100g,
            fiber_g_100g=nutrients.fiber_g_100g,
            similarity_score=score,
            source=food.source,
            is_verified=food.is_verified,
        ))

    return SimilarFoodsResponse(
        success=True,
        reference_food=reference_response,
        similar_foods=similar_foods,
        count=len(similar_foods)
    )