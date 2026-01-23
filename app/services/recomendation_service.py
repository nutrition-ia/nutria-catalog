import logging
from typing import List, Optional, Set

from sqlmodel import Session, select

from app.models.food import Food
from app.models.user import UserProfile


logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)."""
    return text.lower().strip()


def _food_matches_restriction(food: Food, restrictions: Set[str]) -> bool:
    """
    Check if a food matches any dietary restriction.
    Returns True if the food should be EXCLUDED.
    """
    if not restrictions:
        return False

    food_name_normalized = _normalize_text(food.name)
    food_category = _normalize_text(food.category) if food.category else ""

    restriction_mappings = {
        "vegetariano": ["carne", "frango", "peixe", "bacon", "presunto", "salsicha", "linguiça", "meat", "chicken", "fish", "beef", "pork"],
        "vegano": ["carne", "frango", "peixe", "leite", "queijo", "ovo", "mel", "manteiga", "iogurte", "meat", "chicken", "fish", "milk", "cheese", "egg", "honey", "butter", "yogurt"],
        "sem_gluten": ["trigo", "centeio", "cevada", "aveia", "pão", "massa", "wheat", "rye", "barley", "oat", "bread", "pasta", "gluten"],
        "sem_lactose": ["leite", "queijo", "iogurte", "manteiga", "creme", "milk", "cheese", "yogurt", "butter", "cream", "lactose"],
        "kosher": ["porco", "bacon", "presunto", "camarão", "lagosta", "pork", "shrimp", "lobster"],
        "halal": ["porco", "bacon", "presunto", "álcool", "pork", "alcohol"],
    }

    for restriction in restrictions:
        restriction_lower = _normalize_text(restriction)
        if restriction_lower in restriction_mappings:
            excluded_terms = restriction_mappings[restriction_lower]
            for term in excluded_terms:
                if term in food_name_normalized or term in food_category:
                    return True

    return False


def _food_contains_allergen(food: Food, allergies: Set[str]) -> bool:
    """
    Check if a food contains any allergen.
    Returns True if the food should be EXCLUDED.
    """
    if not allergies:
        return False

    food_name_normalized = _normalize_text(food.name)
    food_category = _normalize_text(food.category) if food.category else ""

    allergen_mappings = {
        "amendoim": ["amendoim", "peanut"],
        "nozes": ["nozes", "castanha", "amêndoa", "avelã", "nut", "almond", "hazelnut", "walnut", "cashew"],
        "gluten": ["trigo", "centeio", "cevada", "aveia", "pão", "massa", "wheat", "rye", "barley", "oat", "bread", "pasta", "gluten"],
        "lactose": ["leite", "queijo", "iogurte", "manteiga", "creme", "milk", "cheese", "yogurt", "butter", "cream", "lactose"],
        "ovo": ["ovo", "egg"],
        "soja": ["soja", "tofu", "soy"],
        "frutos_do_mar": ["camarão", "lagosta", "caranguejo", "ostra", "mexilhão", "shrimp", "lobster", "crab", "oyster", "mussel", "shellfish"],
        "peixe": ["peixe", "salmão", "atum", "sardinha", "bacalhau", "fish", "salmon", "tuna", "sardine", "cod"],
    }

    for allergy in allergies:
        allergy_lower = _normalize_text(allergy)

        if allergy_lower in food_name_normalized or allergy_lower in food_category:
            return True

        if allergy_lower in allergen_mappings:
            allergen_terms = allergen_mappings[allergy_lower]
            for term in allergen_terms:
                if term in food_name_normalized or term in food_category:
                    return True

    return False


def _food_is_disliked(food: Food, disliked_foods: Set[str]) -> bool:
    """
    Check if a food is in the user's disliked foods list.
    Returns True if the food should be EXCLUDED.
    """
    if not disliked_foods:
        return False

    food_name_normalized = _normalize_text(food.name)

    for disliked in disliked_foods:
        disliked_normalized = _normalize_text(disliked)
        if disliked_normalized in food_name_normalized or food_name_normalized in disliked_normalized:
            return True

    return False


def recommend_foods(
    session: Session,
    profile: UserProfile,
    limit: Optional[int] = 50
) -> List[Food]:
    """
    Recommends foods based on user dietary restrictions, allergies, and disliked foods.

    Filters out foods that:
    - Match dietary restrictions (e.g., meat for vegetarians)
    - Contain allergens the user is allergic to
    - Are in the user's disliked foods list

    Args:
        session: Database session
        profile: UserProfile object containing user preferences
        limit: Maximum number of foods to return (default: 50)

    Returns:
        List of recommended food items that are safe and preferred for the user
    """
    restrictions: Set[str] = set(profile.dietary_restrictions or [])
    allergies: Set[str] = set(profile.allergies or [])
    disliked_foods: Set[str] = set(profile.disliked_foods or [])

    has_filters = bool(restrictions or allergies or disliked_foods)

    if not has_filters:
        logger.info(f"No dietary restrictions for user {profile.id}, returning all foods.")
        statement = select(Food).limit(limit)
        return list(session.exec(statement).all())

    logger.info(
        f"Filtering recommendations for user {profile.id}: "
        f"restrictions={restrictions}, allergies={allergies}, disliked={disliked_foods}"
    )

    all_foods = session.exec(select(Food)).all()

    recommended: List[Food] = []
    for food in all_foods:
        if _food_matches_restriction(food, restrictions):
            continue
        if _food_contains_allergen(food, allergies):
            continue
        if _food_is_disliked(food, disliked_foods):
            continue

        recommended.append(food)

        if limit and len(recommended) >= limit:
            break

    logger.info(f"Returning {len(recommended)} recommended foods for user {profile.id}")
    return recommended


def get_foods_by_category(
    session: Session,
    profile: UserProfile,
    category: str,
    limit: Optional[int] = 20
) -> List[Food]:
    """
    Get recommended foods filtered by category.

    Args:
        session: Database session
        profile: UserProfile object containing user preferences
        category: Food category to filter by
        limit: Maximum number of foods to return

    Returns:
        List of recommended foods in the specified category
    """
    all_recommended = recommend_foods(session, profile, limit=None)

    category_normalized = _normalize_text(category)
    filtered = [
        food for food in all_recommended
        if food.category and _normalize_text(food.category) == category_normalized
    ]

    if limit:
        filtered = filtered[:limit]

    logger.info(f"Returning {len(filtered)} foods in category '{category}' for user {profile.id}")
    return filtered