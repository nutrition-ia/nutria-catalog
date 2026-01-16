from app.database.database import engine
from app.models.food import Food, FoodNutrient
from app.services.embedding_service import EmbeddingService
from sqlmodel import Session, select

def generate_all_embeddings():
    """Gera embeddings para todos os alimentos no banco"""
    embedding_service = EmbeddingService()

    with Session(engine) as session:
        # Buscar todos os alimentos com nutrients
        statement = (
            select(Food, FoodNutrient)
            .join(FoodNutrient, Food.id == FoodNutrient.food_id, isouter=True)
        )
        results = session.exec(statement).all()

        for food, nutrients in results:
            # Gerar descrição
            description = embedding_service.generate_food_description(food, nutrients)

            # Gerar embedding
            embedding = embedding_service.generate_embedding(description)

            # Atualizar alimento
            food.embedding = embedding
            session.add(food)

        session.commit()
        print(f"Embeddings gerados para {len(results)} alimentos")

if __name__ == "__main__":
    generate_all_embeddings()