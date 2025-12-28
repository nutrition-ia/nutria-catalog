from typing import List, Optional
from sqlmodel import Session, select, or_, and_, col
from uuid import UUID
from decimal import Decimal

from app.models.food import Food, FoodNutrient
from app.schemas.food import FoodSearchFilters, FoodSimpleResponse


class FoodService:
    """Service for food-related operations"""

    def __init__(self, session: Session):
        self.session = session

    def search_foods(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[FoodSearchFilters] = None
    ) -> List[Food]:
        """
        Search for foods using text-based search with optional filters

        Args:
            query: Search query string
            limit: Maximum number of results to return
            filters: Optional filters for category, nutrients, etc.

        Returns:
            List of Food objects matching the search criteria
        """
        # Start with base query
        statement = select(Food).join(FoodNutrient, Food.id == FoodNutrient.food_id, isouter=True)

        # Text search on name and name_normalized (case-insensitive)
        search_term = f"%{query.lower()}%"
        statement = statement.where(
            or_(
                col(Food.name).ilike(search_term),
                col(Food.name_normalized).ilike(search_term)
            )
        )

        # Apply filters if provided
        if filters:
            if filters.category:
                statement = statement.where(Food.category == filters.category)

            if filters.source:
                statement = statement.where(Food.source == filters.source)

            if filters.verified_only:
                statement = statement.where(Food.is_verified == True)

            if filters.min_protein is not None:
                statement = statement.where(
                    FoodNutrient.protein_g_100g >= filters.min_protein
                )

            if filters.max_calories is not None:
                statement = statement.where(
                    or_(
                        Food.calorie_per_100g <= filters.max_calories,
                        FoodNutrient.calories_100g <= filters.max_calories
                    )
                )

        # Limit results
        statement = statement.limit(limit)

        # Execute and return results
        results = self.session.exec(statement).all()
        return list(results)

    def get_food_by_id(self, food_id: UUID) -> Optional[Food]:
        """
        Get a food item by its ID

        Args:
            food_id: UUID of the food item

        Returns:
            Food object if found, None otherwise
        """
        statement = select(Food).where(Food.id == food_id)
        return self.session.exec(statement).first()

    def get_foods_by_ids(self, food_ids: List[UUID]) -> List[Food]:
        """
        Get multiple food items by their IDs

        Args:
            food_ids: List of food UUIDs

        Returns:
            List of Food objects
        """
        statement = select(Food).where(col(Food.id).in_(food_ids))
        results = self.session.exec(statement).all()
        return list(results)

    def get_food_with_nutrients(self, food_id: UUID) -> Optional[Food]:
        """
        Get a food item with its nutrients

        Args:
            food_id: UUID of the food item

        Returns:
            Food object with nutrients if found, None otherwise
        """
        statement = (
            select(Food)
            .where(Food.id == food_id)
            .join(FoodNutrient, Food.id == FoodNutrient.food_id, isouter=True)
        )
        return self.session.exec(statement).first()
