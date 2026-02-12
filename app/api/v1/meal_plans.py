from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.dependencies import get_db
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanListResponse,
    MealPlanResponse,
    MealPlanUpdate,
)
from app.services import meal_plan_service

router = APIRouter()


@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    user_id: UUID,
    request: MealPlanCreate,
    db: Session = Depends(get_db),
) -> MealPlanResponse:
    """
    Create a new meal plan for a user

    This endpoint creates a personalized meal plan with daily nutritional targets.
    The plan can be created manually by the user or automatically by the AI.

    **Query Parameters:**
    - `user_id`: UUID of the user (required)

    **Request Body:**
    - `plan_name`: Name of the meal plan (required, max 100 chars)
    - `description`: Description of the plan (optional, max 500 chars)
    - `daily_calories`: Daily calorie target (required, must be > 0)
    - `daily_protein_g`: Daily protein target in grams (required, must be > 0)
    - `daily_fat_g`: Daily fat target in grams (required, must be > 0)
    - `daily_carbs_g`: Daily carbs target in grams (required, must be > 0)
    - `created_by`: "user" or "ai" (default: "user")
    - `meals`: Array of meal objects (optional, default: [])

    **Response:**
    - Full meal plan object with all fields and timestamps

    **Example Request:**
    ```json
    {
        "plan_name": "Dieta 2000 Calorias",
        "description": "Plano para manutenção de peso com foco em proteínas",
        "daily_calories": 2000.0,
        "daily_protein_g": 150.0,
        "daily_fat_g": 65.0,
        "daily_carbs_g": 200.0,
        "created_by": "ai"
    }
    ```
    """
    try:
        meal_plan = meal_plan_service.create_meal_plan(db, user_id, request)
        return MealPlanResponse.model_validate(meal_plan)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating meal plan: {str(e)}",
        )


@router.get("/", response_model=MealPlanListResponse)
async def list_meal_plans(
    user_id: UUID,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> MealPlanListResponse:
    """
    List all meal plans for a user with pagination

    Retrieves all meal plans created by or for a user, ordered by creation date (newest first).

    **Query Parameters:**
    - `user_id`: UUID of the user (required)
    - `page`: Page number (default: 1, min: 1)
    - `page_size`: Items per page (default: 10, min: 1, max: 100)

    **Response:**
    - `plans`: Array of meal plan objects
    - `total`: Total number of plans for this user
    - `page`: Current page number
    - `page_size`: Items per page

    **Example Response:**
    ```json
    {
        "plans": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440001",
                "plan_name": "Dieta 2000 Calorias",
                "description": "Plano para manutenção de peso",
                "daily_calories": 2000.0,
                "daily_protein_g": 150.0,
                "daily_fat_g": 65.0,
                "daily_carbs_g": 200.0,
                "created_by": "ai",
                "meals": [],
                "created_at": "2024-01-27T10:00:00Z",
                "updated_at": "2024-01-27T10:00:00Z"
            }
        ],
        "total": 5,
        "page": 1,
        "page_size": 10
    }
    ```
    """
    try:
        return meal_plan_service.list_meal_plans(db, user_id, page, page_size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing meal plans: {str(e)}",
        )


@router.get("/{plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(
    plan_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
) -> MealPlanResponse:
    """
    Get a specific meal plan by ID

    Retrieves detailed information about a specific meal plan.
    User ownership is validated - users can only access their own plans.

    **Path Parameters:**
    - `plan_id`: UUID of the meal plan

    **Query Parameters:**
    - `user_id`: UUID of the user (required, for ownership validation)

    **Response:**
    - Full meal plan object with all fields and timestamps

    **Errors:**
    - `404 Not Found`: Meal plan not found or user doesn't own this plan
    """
    meal_plan = meal_plan_service.get_meal_plan(db, plan_id, user_id)

    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )

    return MealPlanResponse.model_validate(meal_plan)


@router.put("/{plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    plan_id: UUID,
    user_id: UUID,
    request: MealPlanUpdate,
    db: Session = Depends(get_db),
) -> MealPlanResponse:
    """
    Update an existing meal plan

    Updates one or more fields of an existing meal plan.
    Only provided fields will be updated - all fields are optional.
    User ownership is validated.

    **Path Parameters:**
    - `plan_id`: UUID of the meal plan

    **Query Parameters:**
    - `user_id`: UUID of the user (required, for ownership validation)

    **Request Body:**
    All fields are optional - only provided fields will be updated:
    - `plan_name`: New name (max 100 chars)
    - `description`: New description (max 500 chars)
    - `daily_calories`: New calorie target (must be > 0)
    - `daily_protein_g`: New protein target (must be > 0)
    - `daily_fat_g`: New fat target (must be > 0)
    - `daily_carbs_g`: New carbs target (must be > 0)
    - `meals`: New meals array

    **Response:**
    - Updated meal plan object with all fields

    **Errors:**
    - `404 Not Found`: Meal plan not found or user doesn't own this plan

    **Example Request:**
    ```json
    {
        "daily_calories": 1800.0,
        "daily_protein_g": 140.0
    }
    ```
    """
    meal_plan = meal_plan_service.update_meal_plan(db, plan_id, user_id, request)

    if not meal_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )

    return MealPlanResponse.model_validate(meal_plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    plan_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a meal plan

    Permanently deletes a meal plan.
    User ownership is validated - users can only delete their own plans.

    **Path Parameters:**
    - `plan_id`: UUID of the meal plan

    **Query Parameters:**
    - `user_id`: UUID of the user (required, for ownership validation)

    **Response:**
    - `204 No Content`: Meal plan successfully deleted

    **Errors:**
    - `404 Not Found`: Meal plan not found or user doesn't own this plan
    """
    success = meal_plan_service.delete_meal_plan(db, plan_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found",
        )
