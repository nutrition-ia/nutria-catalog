from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from app.models.food import FoodSource


# ========== Food Schemas ==========

class FoodNutrientBase(BaseModel):
    """Base schema for food nutrients"""
    calories_100g: Optional[Decimal] = None
    protein_g_100g: Optional[Decimal] = None
    carbs_g_100g: Optional[Decimal] = None
    fat_g_100g: Optional[Decimal] = None
    saturated_fat_g_100g: Optional[Decimal] = None
    fiber_g_100g: Optional[Decimal] = None
    sugar_g_100g: Optional[Decimal] = None
    sodium_mg_100g: Optional[Decimal] = None
    calcium_mg_100g: Optional[Decimal] = None
    iron_mg_100g: Optional[Decimal] = None
    vitamin_c_mg_100g: Optional[Decimal] = None


class FoodNutrientResponse(FoodNutrientBase):
    """Response schema for food nutrients"""
    id: UUID
    food_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FoodBase(BaseModel):
    """Base schema for food"""
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    serving_size_g: Decimal = Field(default=100, ge=0)
    serving_unit: str = Field(default="g", max_length=20)
    calorie_per_100g: Optional[Decimal] = Field(None, ge=0)


class FoodResponse(FoodBase):
    """Response schema for food with nutrients"""
    id: UUID
    name_normalized: str
    usda_id: Optional[str] = None
    source: FoodSource
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    nutrients: Optional[FoodNutrientResponse] = None

    class Config:
        from_attributes = True


class FoodSimpleResponse(BaseModel):
    """Simplified food response for search results"""
    id: UUID
    name: str
    category: Optional[str]
    serving_size_g: Decimal
    serving_unit: str
    calorie_per_100g: Optional[Decimal]
    source: FoodSource
    is_verified: bool

    # Include key nutrients for quick reference
    protein_g_100g: Optional[Decimal] = None
    carbs_g_100g: Optional[Decimal] = None
    fat_g_100g: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ========== Search Schemas ==========

class FoodSearchFilters(BaseModel):
    """Filters for food search"""
    category: Optional[str] = Field(None, description="Filter by food category")
    min_protein: Optional[Decimal] = Field(None, ge=0, description="Minimum protein in grams per 100g")
    max_calories: Optional[Decimal] = Field(None, ge=0, description="Maximum calories per 100g")
    source: Optional[FoodSource] = Field(None, description="Filter by data source")
    verified_only: bool = Field(False, description="Only return verified foods")


class FoodSearchRequest(BaseModel):
    """Request schema for food search"""
    query: str = Field(..., min_length=1, max_length=255, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    filters: Optional[FoodSearchFilters] = Field(None, description="Optional filters")

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class FoodSearchResponse(BaseModel):
    """Response schema for food search"""
    success: bool = True
    foods: List[FoodSimpleResponse]
    count: int = Field(..., description="Number of results returned")


# ========== Nutrition Calculation Schemas ==========

class FoodQuantity(BaseModel):
    """Schema for food with quantity for nutrition calculation"""
    food_id: UUID = Field(..., description="UUID of the food item")
    quantity: Decimal = Field(..., gt=0, description="Quantity in grams")

    @field_validator('quantity')
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class NutritionCalculationRequest(BaseModel):
    """Request schema for nutrition calculation"""
    foods: List[FoodQuantity] = Field(..., min_length=1, description="List of foods with quantities")

    @field_validator('foods')
    @classmethod
    def foods_not_empty(cls, v: List[FoodQuantity]) -> List[FoodQuantity]:
        if not v:
            raise ValueError('At least one food item is required')
        return v


class NutritionTotals(BaseModel):
    """Total nutritional values"""
    calories: Decimal = Field(default=0, description="Total calories")
    protein_g: Decimal = Field(default=0, description="Total protein in grams")
    carbs_g: Decimal = Field(default=0, description="Total carbohydrates in grams")
    fat_g: Decimal = Field(default=0, description="Total fat in grams")
    saturated_fat_g: Decimal = Field(default=0, description="Total saturated fat in grams")
    fiber_g: Decimal = Field(default=0, description="Total fiber in grams")
    sugar_g: Decimal = Field(default=0, description="Total sugar in grams")
    sodium_mg: Decimal = Field(default=0, description="Total sodium in milligrams")
    calcium_mg: Decimal = Field(default=0, description="Total calcium in milligrams")
    iron_mg: Decimal = Field(default=0, description="Total iron in milligrams")
    vitamin_c_mg: Decimal = Field(default=0, description="Total vitamin C in milligrams")


class NutritionDetail(BaseModel):
    """Detailed nutrition for a single food item"""
    food_id: UUID
    food_name: str
    quantity_g: Decimal
    calories: Decimal
    protein_g: Decimal
    carbs_g: Decimal
    fat_g: Decimal


class NutritionCalculationResponse(BaseModel):
    """Response schema for nutrition calculation"""
    success: bool = True
    total: NutritionTotals
    details: List[NutritionDetail]


# ========== Similar Foods Schemas ==========

class SimilarFoodRequest(BaseModel):
    """Request schema for finding similar foods using vector similarity"""
    food_id: UUID = Field(..., description="UUID of the reference food")
    limit: int = Field(default=10, ge=1, le=50, description="Number of similar foods to return")
    same_category: bool = Field(default=False, description="Only return foods from same category")


class SimilarFoodItem(BaseModel):
    """A similar food item with similarity score"""
    id: UUID
    name: str
    category: Optional[str]
    calorie_per_100g: Optional[Decimal]
    protein_g_100g: Optional[Decimal]
    carbs_g_100g: Optional[Decimal]
    fat_g_100g: Optional[Decimal]
    fiber_g_100g: Optional[Decimal]
    similarity_score: Decimal = Field(..., description="Similarity score (0-1, higher is more similar)")
    source: FoodSource
    is_verified: bool

    class Config:
        from_attributes = True


class SimilarFoodsResponse(BaseModel):
    """Response schema for similar foods search"""
    success: bool = True
    reference_food: FoodSimpleResponse
    similar_foods: List[SimilarFoodItem]
    count: int
