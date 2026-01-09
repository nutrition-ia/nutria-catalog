from decimal import Decimal
from typing import TYPE_CHECKING

from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from app.models.food import Food, FoodNutrient


# Thresholds ANVISA (RDC 429/2020) - por 100g de alimento sólido
class AnvisaThresholds:
    # Proteína
    HIGH_PROTEIN = Decimal("12")      # Alto teor de proteína
    SOURCE_PROTEIN = Decimal("6")     # Fonte de proteína

    # Fibras
    HIGH_FIBER = Decimal("6")         # Alto teor de fibras
    SOURCE_FIBER = Decimal("3")       # Fonte de fibras

    # Gorduras
    LOW_FAT = Decimal("3")            # Baixo teor de gordura
    LOW_SATURATED_FAT = Decimal("1.5")  # Baixo teor de gordura saturada

    # Açúcares e sódio
    LOW_SUGAR = Decimal("5")          # Baixo teor de açúcar
    LOW_SODIUM = Decimal("120")       # Baixo teor de sódio

    # Calorias (não é ANVISA oficial, mas útil)
    LOW_CALORIE = Decimal("40")       # Baixa caloria


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate a vector embedding for the given text using the SentenceTransformer model.

        Args:
            text: The input text to generate an embedding for.

        Returns:
            A list of floats representing the vector embedding.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_food_description(self, food: "Food", nutrients: "FoodNutrient") -> str:
        """
        Cria descrição rica do alimento para embedding baseada nos thresholds ANVISA.

        Args:
            food: O alimento
            nutrients: Os nutrientes do alimento

        Returns:
            Descrição textual enriquecida para gerar embedding semântico
        """
        parts = [food.name]

        if food.category:
            parts.append(food.category)

        if nutrients:
            # Proteína
            if nutrients.protein_g_100g:
                if nutrients.protein_g_100g >= AnvisaThresholds.HIGH_PROTEIN:
                    parts.append("alto teor de proteína")
                elif nutrients.protein_g_100g >= AnvisaThresholds.SOURCE_PROTEIN:
                    parts.append("fonte de proteína")

            # Fibras
            if nutrients.fiber_g_100g:
                if nutrients.fiber_g_100g >= AnvisaThresholds.HIGH_FIBER:
                    parts.append("alto teor de fibras")
                elif nutrients.fiber_g_100g >= AnvisaThresholds.SOURCE_FIBER:
                    parts.append("fonte de fibras")

            # Gordura
            if nutrients.fat_g_100g is not None:
                if nutrients.fat_g_100g <= AnvisaThresholds.LOW_FAT:
                    parts.append("baixo teor de gordura")

            # Gordura saturada
            if nutrients.saturated_fat_g_100g is not None:
                if nutrients.saturated_fat_g_100g <= AnvisaThresholds.LOW_SATURATED_FAT:
                    parts.append("baixo teor de gordura saturada")

            # Açúcar
            if nutrients.sugar_g_100g is not None:
                if nutrients.sugar_g_100g <= AnvisaThresholds.LOW_SUGAR:
                    parts.append("baixo teor de açúcar")

            # Sódio
            if nutrients.sodium_mg_100g is not None:
                if nutrients.sodium_mg_100g <= AnvisaThresholds.LOW_SODIUM:
                    parts.append("baixo teor de sódio")

            # Calorias
            if nutrients.calories_100g is not None:
                if nutrients.calories_100g <= AnvisaThresholds.LOW_CALORIE:
                    parts.append("baixa caloria")

        return parts.strip().replace("  ", " ")
