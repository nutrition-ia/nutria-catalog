from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies import get_db
from app.schemas.food import (
    FoodSearchRequest,
    FoodSearchResponse,
    FoodSimpleResponse,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    SimilarFoodItem,
    SimilarFoodRequest,
    SimilarFoodsResponse,
)
from app.services import food_service, food_analysis_service

router = APIRouter()


@router.post("/search", response_model=FoodSearchResponse)
async def search_foods(
    request: FoodSearchRequest, db: Session = Depends(get_db)
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
    foods = food_service.search_foods(
        session=db, query=request.query, limit=request.limit, filters=request.filters
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
        if hasattr(food, "nutrients") and food.nutrients:
            food_dict["protein_g_100g"] = food.nutrients.protein_g_100g
            food_dict["carbs_g_100g"] = food.nutrients.carbs_g_100g
            food_dict["fat_g_100g"] = food.nutrients.fat_g_100g

        simple_foods.append(FoodSimpleResponse(**food_dict))

    return FoodSearchResponse(success=True, foods=simple_foods, count=len(simple_foods))


@router.get("/{food_id}", response_model=FoodSimpleResponse)
async def get_food_by_id(
    food_id: UUID, db: Session = Depends(get_db)
) -> FoodSimpleResponse:
    """
    Get a single food item by ID with full nutritional information.

    **Path Parameters:**
    - `food_id`: UUID of the food item

    **Response:**
    - Food object with complete nutritional data

    **Example:**
    ```
    GET /api/v1/foods/550e8400-e29b-41d4-a716-446655440000
    ```
    """
    food = food_service.get_food_with_nutrients(db, food_id)

    if not food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alimento com ID {food_id} não encontrado",
        )

    # Build response with nutrients
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
    if hasattr(food, "nutrients") and food.nutrients:
        food_dict["protein_g_100g"] = food.nutrients.protein_g_100g
        food_dict["carbs_g_100g"] = food.nutrients.carbs_g_100g
        food_dict["fat_g_100g"] = food.nutrients.fat_g_100g

    return FoodSimpleResponse(**food_dict)


@router.post("/search-by-embedding", response_model=SimilarFoodsResponse)
async def search_foods_by_embedding(
    request: FoodSearchRequest, db: Session = Depends(get_db)
) -> SimilarFoodsResponse:
    """
    Search for foods using semantic similarity (embedding-based search).

    This endpoint generates an embedding for the search query and finds foods
    with similar embeddings using cosine similarity (pgvector). More effective
    than text-based search for complex descriptions like "chicken in creamy sauce".

    **How it works:**
    1. Generates embedding vector for your search query
    2. Compares against all food embeddings in database using cosine distance
    3. Returns top matches ordered by similarity score (0-1, higher is better)

    **Request Body:**
    - `query`: Search string in English (required)
    - `limit`: Maximum number of results (default: 10, max: 50)
    - `filters`: Optional filters (same as /search endpoint)

    **Response:**
    - `success`: Boolean indicating success
    - `reference_food`: Not used (null) - kept for API compatibility
    - `similar_foods`: Array of matching foods with similarity scores
    - `count`: Number of results found

    **Use Cases:**
    - Complex food descriptions: "grilled chicken with herbs"
    - Misspellings or variations: "chiken", "pollo"
    - Semantic matching: "protein source" finds chicken, beef, eggs
    - Cross-language: embeddings can match similar concepts

    **Example Request:**
    ```json
    {
        "query": "chicken in creamy sauce",
        "limit": 5,
        "filters": {
            "category": "protein",
            "verified_only": true
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "reference_food": null,
        "similar_foods": [
            {
                "id": "uuid",
                "name": "Chicken, creamy sauce",
                "similarity_score": 0.9234,
                ...
            }
        ],
        "count": 5
    }
    ```
    """
    # Use embedding-based search
    similar_results = food_service.search_foods_by_embedding(
        session=db,
        query=request.query,
        limit=request.limit,
        filters=request.filters,
    )

    # Build similar foods response
    similar_foods = []
    for food, score in similar_results:
        # Get nutrients if available
        nutrients = None
        if hasattr(food, "nutrients"):
            nutrients = food.nutrients

        similar_foods.append(
            SimilarFoodItem(
                id=food.id,
                name=food.name,
                category=food.category,
                calorie_per_100g=food.calorie_per_100g,
                protein_g_100g=nutrients.protein_g_100g if nutrients else None,
                carbs_g_100g=nutrients.carbs_g_100g if nutrients else None,
                fat_g_100g=nutrients.fat_g_100g if nutrients else None,
                fiber_g_100g=nutrients.fiber_g_100g if nutrients else None,
                similarity_score=score,
                source=food.source,
                is_verified=food.is_verified,
            )
        )

    # Reference food is null since we're searching by text, not by food_id
    return SimilarFoodsResponse(
        success=True,
        reference_food=None,  # type: ignore
        similar_foods=similar_foods,
        count=len(similar_foods),
    )


@router.post("/similar", response_model=SimilarFoodsResponse)
async def find_similar_foods(
    request: SimilarFoodRequest, db: Session = Depends(get_db)
) -> SimilarFoodsResponse:
    """
    Find similar foods using vector similarity search (pgvector).

    This endpoint uses semantic embeddings to find foods with similar
    nutritional profiles and characteristics. Much faster and more
    scalable than traditional comparison methods.

    **Request Body:**
    - `food_id`: UUID of the reference food (required)
    - `limit`: Maximum number of similar foods to return (default: 10, max: 50)
    - `same_category`: Only return foods from the same category (default: false)

    **Response:**
    - `success`: Boolean indicating success
    - `reference_food`: The original food being compared
    - `similar_foods`: Array of similar foods with similarity scores
    - `count`: Number of similar foods found

    **Similarity Calculation:**
    Uses cosine similarity on vector embeddings that encode:
    - Food name and category
    - Nutritional profile (protein, fiber, fat, sugar, sodium, calories)
    - ANVISA nutritional classifications (high protein, low fat, etc.)

    **Example Request:**
    ```json
    {
        "food_id": "uuid-here",
        "limit": 10,
        "same_category": false
    }
    ```
    """
    # Get reference food
    ref_food = food_service.get_food_with_nutrients(db, request.food_id)
    if not ref_food:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Food with ID {request.food_id} not found",
        )

    # Find similar foods using vector search
    similar_results = food_service.find_similar_foods(
        session=db,
        food_id=request.food_id,
        limit=request.limit,
        same_category=request.same_category,
    )

    # Build reference food response
    ref_nutrients = ref_food.nutrients if hasattr(ref_food, "nutrients") else None
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
    for food, score in similar_results:
        nutrients = food.nutrients if hasattr(food, "nutrients") else None
        similar_foods.append(
            SimilarFoodItem(
                id=food.id,
                name=food.name,
                category=food.category,
                calorie_per_100g=food.calorie_per_100g,
                protein_g_100g=nutrients.protein_g_100g if nutrients else None,
                carbs_g_100g=nutrients.carbs_g_100g if nutrients else None,
                fat_g_100g=nutrients.fat_g_100g if nutrients else None,
                fiber_g_100g=nutrients.fiber_g_100g if nutrients else None,
                similarity_score=score,
                source=food.source,
                is_verified=food.is_verified,
            )
        )

    return SimilarFoodsResponse(
        success=True,
        reference_food=reference_response,
        similar_foods=similar_foods,
        count=len(similar_foods),
    )


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_food_image(
    request: ImageAnalysisRequest, db: Session = Depends(get_db)
) -> ImageAnalysisResponse:
    """
    Analyze a food image using DETIC (Detecting Twenty-thousand Classes) and match
    with catalog foods using semantic embeddings.

    **How it works:**
    1. **DETIC Detection**: Open-vocabulary object detection identifies foods in the image
       - Supports 21,000+ categories using CLIP-based embeddings
       - Custom food vocabulary optimized for common foods (fruits, vegetables, proteins, etc.)
       - Returns confidence scores for each detection

    2. **Semantic Matching**: For each detected food, generates embeddings and searches
       the catalog using vector similarity (cosine distance via pgvector)
       - Matches similar foods even with different names (e.g., "apple" → "Maçã Gala")
       - Returns top-k most similar catalog items per detection

    3. **Smart Filtering**: Combines visual detection with nutritional similarity

    **Request Body:**
    - `image`: Base64-encoded image (with or without data:image prefix)
    - `top_k_per_food`: Number of catalog matches per detected food (default: 3, max: 10)
    - `confidence_threshold`: Minimum DETIC confidence (default: 0.5, range: 0.1-1.0)

    **Response:**
    - `success`: Boolean indicating success
    - `detected_foods`: List of food names detected by DETIC (e.g., ["banana", "apple"])
    - `catalog_matches`: Array of matches for each detected food
    - `total_detected`: Total number of unique foods detected
    - `total_catalog_matches`: Total catalog matches found
    - `message`: Optional message (e.g., when no foods detected)

    **Use Cases:**
    - Meal logging: Take a photo of your plate and auto-populate food entries
    - Recipe analysis: Identify ingredients from a recipe photo
    - Nutrition estimation: Quick calorie/macro estimates from food photos

    **Requirements:**
    - DETIC model must be installed and configured (set DETIC_MODEL_PATH env var)
    - pgvector extension enabled in PostgreSQL
    - Food embeddings pre-generated in the catalog

    **Fallback Behavior:**
    - If DETIC is not available, returns empty detections with success=true
    - If no foods detected, returns empty catalog_matches with appropriate message

    **Example Request:**
    ```json
    {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...",
        "top_k_per_food": 3,
        "confidence_threshold": 0.5
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "detected_foods": ["banana", "apple"],
        "catalog_matches": [
            {
                "detected_name": "banana",
                "matches": [
                    {
                        "id": "uuid-here",
                        "name": "Banana Prata",
                        "similarity": 0.95,
                        "category": "frutas",
                        "calories_per_100g": 89,
                        "serving_size_g": 100,
                        "serving_unit": "g",
                        "source": "taco",
                        "is_verified": true
                    }
                ]
            }
        ],
        "total_detected": 2,
        "total_catalog_matches": 6
    }
    ```

    **Performance Notes:**
    - First request: ~2-5s (model loading + inference)
    - Subsequent requests: ~0.5-1.5s (model cached, only inference)
    - Embedding search: O(n) with pgvector index, very fast even with large catalogs
    """
    try:
        result = await food_analysis_service.analyze_food_image(
            session=db,
            base64_image=request.image,
            top_k_per_food=request.top_k_per_food,
            confidence_threshold=request.confidence_threshold,
        )
        return ImageAnalysisResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na análise de imagem: {str(e)}",
        )
