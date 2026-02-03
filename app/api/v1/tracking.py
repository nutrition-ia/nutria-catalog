from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies import get_db
from app.schemas.tracking import (
    DailySummaryResponse,
    MealLogRequest,
    MealLogResponse,
    WeeklyStatsResponse,
)
from app.services import tracking_service

router = APIRouter()


@router.post("/meals/log", response_model=MealLogResponse, status_code=status.HTTP_201_CREATED)
async def log_meal(
    request: MealLogRequest, db: Session = Depends(get_db)
) -> MealLogResponse:
    """
    Log a meal consumed by the user

    This endpoint registers a meal with all foods consumed and their quantities.
    It automatically calculates nutritional totals and updates daily statistics.

    **Request Body:**
    - `user_id`: UUID of the user (required)
    - `meal_type`: Type of meal - breakfast, lunch, dinner, snack (required)
    - `foods`: Array of food items with quantities (required, min 1 item)
        - `food_id`: UUID of the food item
        - `quantity_g`: Quantity in grams (must be > 0)
        - `name`: Optional display name for the food
    - `consumed_at`: When the meal was consumed (optional, defaults to now)
    - `notes`: User notes about the meal (optional, max 500 chars)

    **Response:**
    - `id`: UUID of the created meal log
    - `user_id`: UUID of the user
    - `consumed_at`: When the meal was consumed
    - `meal_type`: Type of meal
    - `foods`: Array of food items consumed
    - `total_calories`: Total calories for this meal
    - `total_protein_g`: Total protein in grams
    - `total_carbs_g`: Total carbs in grams
    - `total_fat_g`: Total fat in grams
    - `total_fiber_g`: Total fiber in grams (if available)
    - `total_sodium_mg`: Total sodium in mg (if available)
    - `notes`: User notes
    - `created_at`: When the log was created

    **Example Request:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "meal_type": "breakfast",
        "foods": [
            {
                "food_id": "650e8400-e29b-41d4-a716-446655440001",
                "quantity_g": 50,
                "name": "Aveia"
            },
            {
                "food_id": "650e8400-e29b-41d4-a716-446655440002",
                "quantity_g": 200,
                "name": "Leite desnatado"
            }
        ],
        "notes": "Café da manhã pós-treino"
    }
    ```

    **Example Response:**
    ```json
    {
        "id": "750e8400-e29b-41d4-a716-446655440003",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "consumed_at": "2024-01-27T08:30:00Z",
        "meal_type": "breakfast",
        "foods": [...],
        "total_calories": 320.5,
        "total_protein_g": 18.2,
        "total_carbs_g": 45.3,
        "total_fat_g": 5.1,
        "total_fiber_g": 4.2,
        "total_sodium_mg": 125.0,
        "notes": "Café da manhã pós-treino",
        "created_at": "2024-01-27T08:35:00Z"
    }
    ```
    """
    try:
        meal_log = tracking_service.log_meal(db, request)
        return meal_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging meal: {str(e)}",
        )


@router.get("/summary/daily", response_model=DailySummaryResponse)
async def get_daily_summary(
    user_id: UUID,
    date: date = date.today(),
    db: Session = Depends(get_db),
) -> DailySummaryResponse:
    """
    Get daily nutrition summary for a user

    This endpoint returns a complete summary of all meals logged for a specific day,
    including totals, targets, and progress towards goals.

    **Query Parameters:**
    - `user_id`: UUID of the user (required)
    - `date`: Date to get summary for (optional, defaults to today)
        - Format: YYYY-MM-DD (e.g., 2024-01-27)

    **Response:**
    - `date`: The date of the summary
    - `meals`: Array of meal summaries for the day
        - `id`: UUID of the meal log
        - `meal_type`: Type of meal
        - `consumed_at`: When it was consumed
        - `total_calories`: Calories for this meal
        - `total_protein_g`: Protein for this meal
        - `total_carbs_g`: Carbs for this meal
        - `total_fat_g`: Fat for this meal
        - `num_foods`: Number of foods in this meal
        - `notes`: User notes
    - `totals`: Total nutrition for the day
        - `calories`: Total calories
        - `protein_g`: Total protein
        - `carbs_g`: Total carbs
        - `fat_g`: Total fat
        - `fiber_g`: Total fiber
        - `sodium_mg`: Total sodium
    - `targets`: User's nutrition targets
        - `calories`: Target calories
        - `protein_g`: Target protein
        - `carbs_g`: Target carbs
        - `fat_g`: Target fat
    - `progress`: Progress towards goals (percentages)
        - `calories_pct`: Percentage of calorie goal reached
        - `protein_pct`: Percentage of protein goal reached
        - `carbs_pct`: Percentage of carbs goal reached
        - `fat_pct`: Percentage of fat goal reached
    - `num_meals`: Total number of meals logged

    **Example Request:**
    ```
    GET /api/v1/tracking/summary/daily?user_id=550e8400-e29b-41d4-a716-446655440000&date=2024-01-27
    ```

    **Example Response:**
    ```json
    {
        "date": "2024-01-27",
        "meals": [
            {
                "id": "750e8400-e29b-41d4-a716-446655440003",
                "meal_type": "breakfast",
                "consumed_at": "2024-01-27T08:30:00Z",
                "total_calories": 320.5,
                "total_protein_g": 18.2,
                "total_carbs_g": 45.3,
                "total_fat_g": 5.1,
                "num_foods": 2,
                "notes": "Café da manhã pós-treino"
            }
        ],
        "totals": {
            "calories": 1850.0,
            "protein_g": 142.5,
            "carbs_g": 185.2,
            "fat_g": 62.3,
            "fiber_g": 28.5,
            "sodium_mg": 2100.0
        },
        "targets": {
            "calories": 2000.0,
            "protein_g": 150.0,
            "carbs_g": 250.0,
            "fat_g": 67.0
        },
        "progress": {
            "calories_pct": 92.5,
            "protein_pct": 95.0,
            "carbs_pct": 74.1,
            "fat_pct": 93.0
        },
        "num_meals": 3
    }
    ```
    """
    try:
        summary = tracking_service.get_daily_summary(db, user_id, date)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting daily summary: {str(e)}",
        )


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats(
    user_id: UUID,
    days: int = 7,
    db: Session = Depends(get_db),
) -> WeeklyStatsResponse:
    """
    Get weekly nutrition statistics for a user

    This endpoint returns aggregated statistics for a specified period,
    including daily breakdown and averages.

    **Query Parameters:**
    - `user_id`: UUID of the user (required)
    - `days`: Number of days to include (optional, default 7, min 1, max 30)

    **Response:**
    - `user_id`: UUID of the user
    - `stats`: Array of daily statistics
        - `date`: The date
        - `total_calories`: Total calories for the day
        - `total_protein_g`: Total protein
        - `total_carbs_g`: Total carbs
        - `total_fat_g`: Total fat
        - `num_meals`: Number of meals logged
        - `target_calories`: Target calories (if available)
        - `target_protein_g`: Target protein (if available)
    - `averages`: Average nutrition over the period
        - `calories`: Average daily calories
        - `protein_g`: Average daily protein
        - `carbs_g`: Average daily carbs
        - `fat_g`: Average daily fat
    - `adherence_rate`: Percentage of days with logged meals

    **Example Request:**
    ```
    GET /api/v1/tracking/stats/weekly?user_id=550e8400-e29b-41d4-a716-446655440000&days=7
    ```

    **Example Response:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "stats": [
            {
                "date": "2024-01-21",
                "total_calories": 1950.0,
                "total_protein_g": 145.2,
                "total_carbs_g": 195.3,
                "total_fat_g": 65.1,
                "num_meals": 3,
                "target_calories": 2000.0,
                "target_protein_g": 150.0
            },
            {
                "date": "2024-01-22",
                "total_calories": 2100.0,
                "total_protein_g": 155.8,
                "total_carbs_g": 210.5,
                "total_fat_g": 70.2,
                "num_meals": 4,
                "target_calories": 2000.0,
                "target_protein_g": 150.0
            }
        ],
        "averages": {
            "calories": 1985.5,
            "protein_g": 148.3,
            "carbs_g": 198.7,
            "fat_g": 66.8
        },
        "adherence_rate": 85.7
    }
    ```
    """
    try:
        stats = tracking_service.get_weekly_stats(db, user_id, days)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting weekly stats: {str(e)}",
        )
