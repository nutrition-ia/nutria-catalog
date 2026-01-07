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

    def find_similar_foods(
        self,
        food_id: UUID,
        limit: int = 10,
        same_category: bool = False,
        tolerance: Decimal = Decimal("0.3")
    ) -> List[tuple]:
        """
        Find foods with similar nutritional profile.

        Args:
            food_id: UUID of the reference food
            limit: Maximum number of similar foods to return
            same_category: If True, only return foods from same category
            tolerance: Tolerance for nutritional similarity (0.3 = 30% difference allowed)

        Returns:
            List of tuples (Food, FoodNutrient, similarity_score)
        """
        # Get reference food with nutrients
        ref_food = self.get_food_with_nutrients(food_id)
        if not ref_food:
            return []

        # Get reference nutrients
        ref_nutrients = self.session.exec(
            select(FoodNutrient).where(FoodNutrient.food_id == food_id)
        ).first()

        if not ref_nutrients:
            return []

        # Build query for similar foods
        statement = (
            select(Food, FoodNutrient)
            .join(FoodNutrient, Food.id == FoodNutrient.food_id)
            .where(Food.id != food_id)  # Exclude reference food
        )

        # Filter by category if requested
        if same_category and ref_food.category:
            statement = statement.where(Food.category == ref_food.category)

        # Execute query
        results = self.session.exec(statement).all()

        # Calculate similarity scores
        similar_foods = []
        for food, nutrients in results:
            score = self._calculate_similarity(ref_nutrients, nutrients, tolerance)
            if score > 0:
                similar_foods.append((food, nutrients, score))

        # Sort by similarity score (descending) and limit
        similar_foods.sort(key=lambda x: x[2], reverse=True)
        return similar_foods[:limit]

    def _calculate_similarity(
        self,
        ref: FoodNutrient,
        candidate: FoodNutrient,
        tolerance: Decimal
    ) -> Decimal:
        """
        Calculate nutritional similarity score between two foods.

        Uses weighted comparison of macronutrients:
        - Calories: 30%
        - Protein: 25%
        - Carbs: 20%
        - Fat: 15%
        - Fiber: 10%

        Returns score from 0 to 1 (1 = identical, 0 = too different)
        """
        weights = {
            'calories': Decimal("0.30"),
            'protein': Decimal("0.25"),
            'carbs': Decimal("0.20"),
            'fat': Decimal("0.15"),
            'fiber': Decimal("0.10"),
        }

        def get_nutrient_similarity(ref_val, cand_val, weight):
            """Calculate similarity for a single nutrient."""
            if ref_val is None or cand_val is None:
                return weight * Decimal("0.5")  # Neutral score for missing data

            if ref_val == 0:
                return weight if cand_val == 0 else Decimal("0")

            diff_ratio = abs(ref_val - cand_val) / ref_val
            if diff_ratio > tolerance:
                return Decimal("0")

            # Linear scoring: 1.0 at 0% diff, 0.0 at tolerance
            similarity = Decimal("1") - (diff_ratio / tolerance)
            return weight * similarity

        total_score = Decimal("0")
        total_score += get_nutrient_similarity(
            ref.calories_100g, candidate.calories_100g, weights['calories']
        )
        total_score += get_nutrient_similarity(
            ref.protein_g_100g, candidate.protein_g_100g, weights['protein']
        )
        total_score += get_nutrient_similarity(
            ref.carbs_g_100g, candidate.carbs_g_100g, weights['carbs']
        )
        total_score += get_nutrient_similarity(
            ref.fat_g_100g, candidate.fat_g_100g, weights['fat']
        )
        total_score += get_nutrient_similarity(
            ref.fiber_g_100g, candidate.fiber_g_100g, weights['fiber']
        )

        return total_score.quantize(Decimal("0.01"))
