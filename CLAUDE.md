# FastAPI Production Backend Template

Production-ready FastAPI backend with SQLAlchemy (async) and Alembic for database migrations.

## Project Structure

```
app/
├── api/v1/                 # API layer (versioned)
│   ├── controllers/        # Request handlers - validation & orchestration
│   ├── routes/             # Route definitions with OpenAPI docs
│   └── router.py           # Main router aggregator
├── core/                   # Core configuration
│   ├── config.py           # Settings (Pydantic Settings)
│   ├── exceptions.py       # Custom exception classes
│   └── error_handlers.py   # Global exception handlers
├── db/                     # Database layer
│   ├── base.py             # SQLAlchemy Base and mixins
│   └── session.py          # Async engine and session factory
├── models/                 # SQLAlchemy ORM models
├── schemas/                # Pydantic schemas (request/response)
├── services/               # Business logic layer
└── main.py                 # Application entry point

alembic/                    # Database migrations
├── versions/               # Migration files
├── env.py                  # Alembic async configuration
└── script.py.mako          # Migration template
```

## Quick Start

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Install dependencies with uv
uv sync
```

### 2. Start PostgreSQL

**Option A: Docker Compose (recommended)**
```bash
docker compose up db -d
```

**Option B: Local PostgreSQL**
Ensure PostgreSQL is running and update `.env` with your connection details.

### 3. Run Migrations

```bash
# Apply all migrations
uv run alembic upgrade head

# Check current migration status
uv run alembic current
```

### 4. Start the Server

```bash
# Development mode with hot reload
uv run fastapi dev app/main.py

# Production mode
uv run fastapi run app/main.py
```

API available at: http://localhost:8000
Docs: http://localhost:8000/docs

## Database & Migrations

### Creating New Models

1. Create model in `app/models/`:
```python
# app/models/item.py
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
```

2. Import in `app/models/__init__.py`:
```python
from app.models.item import Item
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "add items table"

# Create empty migration for manual SQL
uv run alembic revision -m "add custom index"
```

### Applying Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade one step
uv run alembic upgrade +1

# Downgrade one step
uv run alembic downgrade -1

# Downgrade to specific revision
uv run alembic downgrade abc123
```

### Migration Tips

- Always review auto-generated migrations before applying
- Keep migrations small and focused
- Test migrations on a copy of production data before deploying

## Adding New Endpoints

Follow the 3-layer pattern: Routes → Controllers → Services

### 1. Create Schema (app/schemas/item.py)
```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str

class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
```

### 2. Create Service (app/services/item_service.py)
```python
class ItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, item_in: ItemCreate) -> Item:
        item = Item(**item_in.model_dump())
        self.db.add(item)
        await self.db.flush()
        return item
```

### 3. Create Controller (app/api/v1/controllers/item_controller.py)
```python
class ItemController:
    def __init__(self, db: AsyncSession):
        self.service = ItemService(db)

    async def create_item(self, item_in: ItemCreate) -> ItemResponse:
        item = await self.service.create(item_in)
        return ItemResponse.model_validate(item)
```

### 4. Create Routes (app/api/v1/routes/item_routes.py)
```python
router = APIRouter(prefix="/items", tags=["Items"])

@router.post("", response_model=ItemResponse)
async def create_item(
    item_in: ItemCreate,
    db: AsyncSession = Depends(get_db),
):
    controller = ItemController(db)
    return await controller.create_item(item_in)
```

### 5. Register in Router (app/api/v1/router.py)
```python
from app.api.v1.routes import item_routes
api_router.include_router(item_routes.router)
```

## Docker

### Development
```bash
# Start all services (db + api)
docker compose up

# Start only database
docker compose up db -d

# Rebuild after dependency changes
docker compose build api
```

### Running Migrations in Docker
```bash
docker compose exec api alembic upgrade head
```

## Common Commands

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Run tests
uv run pytest

# Format code (if configured)
uv run ruff format .

# Lint code (if configured)
uv run ruff check .
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_DB` | Database name | `app` |
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `True` |

## Architecture Notes

- **Async-first**: Uses SQLAlchemy 2.0 async with asyncpg driver
- **Dependency injection**: Database sessions injected via FastAPI Depends
- **UUID primary keys**: All models use UUID strings for IDs
- **Timestamps**: Use `TimestampMixin` for automatic `created_at`/`updated_at`
- **Validation**: Pydantic schemas for all request/response validation
- **Error handling**: Global exception handlers with consistent JSON responses
