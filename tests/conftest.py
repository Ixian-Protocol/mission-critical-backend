"""
Pytest configuration and shared fixtures for Task API tests.
"""
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.tag import Tag
from app.models.task import Task, now_ms


# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for a test.

    Each test gets a fresh session with tables truncated.
    """
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        # Clean up tables before each test
        await session.execute(text("DELETE FROM tasks"))
        await session.execute(text("DELETE FROM tags"))
        await session.commit()

        yield session

        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing the API.

    Overrides the database dependency to use the test session.
    """
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Return sample task data for creating tasks."""
    return {
        "text": "Test task",
        "description": "A test task description",
        "completed": False,
        "important": False,
        "tag": "General",
        "due_at": None,
        "recurrence": "none",
        "recurrence_alt": False,
    }


@pytest.fixture
async def existing_task(db_session: AsyncSession) -> Task:
    """Create an existing task in the database for testing."""
    current_time = now_ms()
    task = Task(
        text="Existing task",
        description="An existing task",
        completed=False,
        important=False,
        tag="General",
        recurrence="none",
        recurrence_alt=False,
        created_at=current_time,
        updated_at=current_time,
    )
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


@pytest.fixture
async def multiple_tasks(db_session: AsyncSession) -> list[Task]:
    """Create multiple tasks with various properties for filtering tests."""
    current_time = now_ms()
    tasks = [
        Task(
            text="Work task 1",
            description="Important work task",
            completed=False,
            important=True,
            tag="Work",
            recurrence="none",
            recurrence_alt=False,
            created_at=current_time,
            updated_at=current_time,
        ),
        Task(
            text="Work task 2",
            description="Completed work task",
            completed=True,
            important=False,
            tag="Work",
            recurrence="none",
            recurrence_alt=False,
            created_at=current_time - 1000,
            updated_at=current_time - 1000,
        ),
        Task(
            text="Personal task",
            description="Personal errand",
            completed=False,
            important=False,
            tag="Personal",
            recurrence="none",
            recurrence_alt=False,
            created_at=current_time - 2000,
            updated_at=current_time - 2000,
        ),
        Task(
            text="Research task",
            description="Important research",
            completed=False,
            important=True,
            tag="Research",
            recurrence="none",
            recurrence_alt=False,
            created_at=current_time - 3000,
            updated_at=current_time - 3000,
        ),
    ]

    for task in tasks:
        db_session.add(task)

    await db_session.flush()

    for task in tasks:
        await db_session.refresh(task)

    return tasks


@pytest.fixture
async def deleted_task(db_session: AsyncSession) -> Task:
    """Create a soft-deleted task for testing."""
    current_time = now_ms()
    task = Task(
        text="Deleted task",
        description="This task has been deleted",
        completed=False,
        important=False,
        tag="General",
        recurrence="none",
        recurrence_alt=False,
        created_at=current_time - 10000,
        updated_at=current_time,
        deleted_at=current_time,
    )
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


# ============================================================================
# Tag Fixtures
# ============================================================================


@pytest.fixture
def sample_tag_data() -> dict[str, Any]:
    """Return sample tag data for creating tags."""
    current_time = now_ms()
    return {
        "name": "Test Tag",
        "color": "#14b8a6",
        "is_default": False,
        "created_at": current_time,
        "updated_at": current_time,
    }


@pytest.fixture
async def existing_tag(db_session: AsyncSession) -> Tag:
    """Create an existing tag in the database for testing."""
    current_time = now_ms()
    tag = Tag(
        name="Existing Tag",
        color="#3b82f6",
        is_default=False,
        created_at=current_time,
        updated_at=current_time,
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.refresh(tag)
    return tag


@pytest.fixture
async def default_tag(db_session: AsyncSession) -> Tag:
    """Create a default tag that cannot be deleted."""
    current_time = now_ms()
    tag = Tag(
        name="General",
        color="#6b7280",
        is_default=True,
        created_at=current_time,
        updated_at=current_time,
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.refresh(tag)
    return tag


@pytest.fixture
async def multiple_tags(db_session: AsyncSession) -> list[Tag]:
    """Create multiple tags for testing list operations."""
    current_time = now_ms()
    tags = [
        Tag(
            name="Work",
            color="#ef4444",
            is_default=True,
            created_at=current_time,
            updated_at=current_time,
        ),
        Tag(
            name="Personal",
            color="#22c55e",
            is_default=True,
            created_at=current_time - 1000,
            updated_at=current_time - 1000,
        ),
        Tag(
            name="Research",
            color="#a855f7",
            is_default=False,
            created_at=current_time - 2000,
            updated_at=current_time - 2000,
        ),
        Tag(
            name="Design",
            color="#f97316",
            is_default=False,
            created_at=current_time - 3000,
            updated_at=current_time - 3000,
        ),
    ]

    for tag in tags:
        db_session.add(tag)

    await db_session.flush()

    for tag in tags:
        await db_session.refresh(tag)

    return tags


@pytest.fixture
async def deleted_tag(db_session: AsyncSession) -> Tag:
    """Create a soft-deleted tag for testing."""
    current_time = now_ms()
    tag = Tag(
        name="Deleted Tag",
        color="#94a3b8",
        is_default=False,
        created_at=current_time - 10000,
        updated_at=current_time,
        deleted_at=current_time,
    )
    db_session.add(tag)
    await db_session.flush()
    await db_session.refresh(tag)
    return tag
