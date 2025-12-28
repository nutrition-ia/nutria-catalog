# Nutria Food Catalog API

A comprehensive food and nutrition database API built with FastAPI and PostgreSQL with pgvector. Designed to be consumed by AI agents (Mastra.ai) for nutritional assistance.

## Features

- **Food Search**: Text-based search with multiple filters (category, nutrients, source, verification status)
- **Nutrition Calculations**: Calculate total nutritional values for food combinations
- **Multi-source Data**: Support for USDA, TACO, and custom food databases
- **Semantic Search Ready**: Infrastructure prepared for pgvector-based semantic search (Phase 2)
- **OpenAPI/Swagger**: Full API documentation available at `/docs`

## Tech Stack

- **Python 3.11** (managed via asdf or pyenv)
- **FastAPI** - Modern, fast web framework
- **SQLModel** - SQL database ORM with Pydantic integration
- **PostgreSQL 15+** with **pgvector** extension
- **Docker & Docker Compose** - Containerized development
- **Alembic** - Database migrations

## Project Structure

```
nutria-catalog/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app and Swagger config
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── food.py             # Food and FoodNutrient models
│   │   └── base.py             # Base models with mixins
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── food.py             # Pydantic schemas
│   │   └── common.py           # Common schemas (pagination, etc)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── foods.py        # Food search endpoints
│   │   │   └── nutrition.py    # Nutrition calculation endpoints
│   │   └── dependencies.py     # FastAPI dependencies
│   └── services/
│       ├── __init__.py
│       ├── food_service.py     # Food business logic
│       ├── nutrition_service.py # Nutrition calculations
│       └── search_service.py   # Semantic search (Phase 2)
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── docker/
│   └── init.sql                # PostgreSQL initialization
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11
- Docker and Docker Compose
- asdf or pyenv (recommended for Python version management)

### Option 1: Setup with asdf (Recommended)

1. **Install asdf** (if not already installed):
   ```bash
   git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
   echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Install Python 3.11 with asdf**:
   ```bash
   asdf plugin add python
   asdf install python 3.11.7
   asdf local python 3.11.7
   ```

3. **Verify Python version**:
   ```bash
   python --version  # Should show Python 3.11.7
   ```

### Option 2: Setup with pyenv

1. **Install pyenv** (if not already installed):
   ```bash
   curl https://pyenv.run | bash
   ```

2. **Install Python 3.11**:
   ```bash
   pyenv install 3.11.7
   pyenv local 3.11.7
   ```

3. **Verify Python version**:
   ```bash
   python --version  # Should show Python 3.11.7
   ```

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   cd nutria-catalog
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env if you need to change database credentials
   ```

5. **Start PostgreSQL with Docker**:
   ```bash
   docker-compose up -d
   ```

6. **Wait for PostgreSQL to be ready**:
   ```bash
   docker-compose logs -f postgres
   # Wait until you see "database system is ready to accept connections"
   # Press Ctrl+C to exit logs
   ```

7. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

8. **Start the API server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

9. **Access the API**:
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check

- `GET /` - API information
- `GET /health` - Health check

### Food Search

**POST /api/v1/foods/search**

Search for food items with text queries and optional filters.

**Request Body:**
```json
{
  "query": "chicken breast",
  "limit": 10,
  "filters": {
    "category": "protein",
    "min_protein": 20,
    "max_calories": 200,
    "source": "usda",
    "verified_only": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "foods": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Chicken Breast, Skinless",
      "category": "protein",
      "serving_size_g": 100,
      "serving_unit": "g",
      "calorie_per_100g": 165,
      "source": "usda",
      "is_verified": true,
      "protein_g_100g": 31,
      "carbs_g_100g": 0,
      "fat_g_100g": 3.6
    }
  ],
  "count": 1
}
```

### Nutrition Calculation

**POST /api/v1/nutrition/calculate**

Calculate total nutritional values for a combination of foods.

**Request Body:**
```json
{
  "foods": [
    {
      "food_id": "550e8400-e29b-41d4-a716-446655440000",
      "quantity": 150
    },
    {
      "food_id": "550e8400-e29b-41d4-a716-446655440001",
      "quantity": 100
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total": {
    "calories": 350.5,
    "protein_g": 45.2,
    "carbs_g": 12.5,
    "fat_g": 8.3,
    "saturated_fat_g": 2.1,
    "fiber_g": 2.5,
    "sugar_g": 1.2,
    "sodium_mg": 150,
    "calcium_mg": 50,
    "iron_mg": 2.5,
    "vitamin_c_mg": 10
  },
  "details": [
    {
      "food_id": "550e8400-e29b-41d4-a716-446655440000",
      "food_name": "Chicken Breast",
      "quantity_g": 150,
      "calories": 247.5,
      "protein_g": 46.5,
      "carbs_g": 0,
      "fat_g": 5.4
    }
  ]
}
```

## Database Schema

### Foods Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Food name |
| name_normalized | VARCHAR(255) | Normalized name for searching |
| category | VARCHAR(50) | Food category |
| serving_size_g | DECIMAL | Default serving size in grams |
| serving_unit | VARCHAR(20) | Unit of measurement |
| calorie_per_100g | DECIMAL | Calories per 100g |
| usda_id | VARCHAR(50) | USDA FoodData Central ID |
| source | ENUM | Data source (usda, taco, custom) |
| is_verified | BOOLEAN | Verification status |
| embedding | VECTOR(384) | Vector embedding for semantic search |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### Food Nutrients Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| food_id | UUID | Foreign key to foods |
| calories_100g | DECIMAL | Calories per 100g |
| protein_g_100g | DECIMAL | Protein in grams per 100g |
| carbs_g_100g | DECIMAL | Carbohydrates in grams per 100g |
| fat_g_100g | DECIMAL | Fat in grams per 100g |
| saturated_fat_g_100g | DECIMAL | Saturated fat in grams per 100g |
| fiber_g_100g | DECIMAL | Fiber in grams per 100g |
| sugar_g_100g | DECIMAL | Sugar in grams per 100g |
| sodium_mg_100g | DECIMAL | Sodium in milligrams per 100g |
| calcium_mg_100g | DECIMAL | Calcium in milligrams per 100g |
| iron_mg_100g | DECIMAL | Iron in milligrams per 100g |
| vitamin_c_mg_100g | DECIMAL | Vitamin C in milligrams per 100g |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

## Development

### Running tests

```bash
# TODO: Add tests in Phase 2
pytest
```

### Code formatting

```bash
# Install formatting tools
pip install black isort

# Format code
black app/
isort app/
```

### Type checking

```bash
# Install mypy
pip install mypy

# Run type checking
mypy app/
```

## Docker Commands

### Start services

```bash
docker-compose up -d
```

### Stop services

```bash
docker-compose down
```

### View logs

```bash
docker-compose logs -f
```

### Restart PostgreSQL

```bash
docker-compose restart postgres
```

### Access PostgreSQL CLI

```bash
docker-compose exec postgres psql -U nutriauser -d nutriadb
```

## Troubleshooting

### PostgreSQL connection issues

1. Ensure Docker is running:
   ```bash
   docker ps
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   ```

3. Verify PostgreSQL is healthy:
   ```bash
   docker-compose exec postgres pg_isready -U nutriauser
   ```

### Migration issues

1. Check current migration status:
   ```bash
   alembic current
   ```

2. Reset database (WARNING: This will delete all data):
   ```bash
   docker-compose down -v
   docker-compose up -d
   alembic upgrade head
   ```

### Import errors

Ensure you're in the virtual environment and all dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Future Enhancements (Phase 2)

- Semantic search using pgvector and sentence-transformers
- Embedding generation for food descriptions
- Hybrid search combining text and semantic search
- Authentication and authorization
- Rate limiting
- Caching layer (Redis)
- Data import scripts for USDA and TACO databases
- Comprehensive test suite
- CI/CD pipeline

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]

## Contact

[Add contact information here]
