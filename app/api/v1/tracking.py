from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.dependencies import get_current_user_id, get_db
from app.schemas.tracking import (
    DailySummaryResponse,
    MealLogRequest,
    MealLogResponse,
    WeeklyStatsResponse,
)
from app.services import tracking_service

router = APIRouter()


@router.post(
    "/meals/log", response_model=MealLogResponse, status_code=status.HTTP_201_CREATED
)
async def log_meal(
    request: MealLogRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> MealLogResponse:
    """
    Log a meal consumed by the authenticated user.

    The user_id is extracted from the JWT token — the user_id field in the
    request body is overridden with the authenticated user's ID for security.
    """
    try:
        # Override user_id with authenticated user
        request.user_id = UUID(current_user_id)
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
    target_date: date = date.today(),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> DailySummaryResponse:
    """
    Get daily nutrition summary for the authenticated user.

    **Query Parameters:**
    - `target_date`: Date to get summary for (optional, defaults to today, format: YYYY-MM-DD)
    """
    try:
        summary = tracking_service.get_daily_summary(
            db, UUID(current_user_id), target_date
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting daily summary: {str(e)}",
        )


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
) -> WeeklyStatsResponse:
    """
    Get weekly nutrition statistics for the authenticated user.

    **Query Parameters:**
    - `days`: Number of days to include (optional, default 7, min 1, max 30)
    """
    try:
        stats = tracking_service.get_weekly_stats(db, UUID(current_user_id), days)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting weekly stats: {str(e)}",
        )
