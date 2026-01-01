# Tags API Specification

This document specifies the REST API endpoints required for the Tags sync backend, complementing the existing Tasks API.

## Overview

Tags are now dynamic and user-configurable. The frontend allows users to create custom tags with auto-assigned colors. Tags sync to the server like tasks.

---

## Database Schema

### Tags Table

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    color VARCHAR(7) NOT NULL,  -- Hex color e.g. '#14b8a6'
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at BIGINT NOT NULL,  -- Unix timestamp in milliseconds
    updated_at BIGINT NOT NULL,  -- Unix timestamp in milliseconds
    deleted_at BIGINT NULL,  -- Soft delete timestamp, NULL if not deleted

    CONSTRAINT unique_tag_name UNIQUE (name)
);

CREATE INDEX idx_tags_updated_at ON tags(updated_at);
CREATE INDEX idx_tags_deleted_at ON tags(deleted_at);
```

### Update Tasks Table

The `tag` column constraint needs to be removed since tags are now dynamic:

```sql
-- Remove the old constraint
ALTER TABLE tasks DROP CONSTRAINT IF EXISTS valid_tag;

-- Change tag column to reference tag names (no foreign key needed, just string)
ALTER TABLE tasks ALTER COLUMN tag TYPE VARCHAR(50);
```

### Seed Default Tags

On first deployment, seed the default tags:

```sql
INSERT INTO tags (id, name, color, is_default, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'General', '#14b8a6', TRUE, EXTRACT(EPOCH FROM NOW()) * 1000, EXTRACT(EPOCH FROM NOW()) * 1000),
    (gen_random_uuid(), 'Work', '#a855f7', TRUE, EXTRACT(EPOCH FROM NOW()) * 1000, EXTRACT(EPOCH FROM NOW()) * 1000),
    (gen_random_uuid(), 'Personal', '#3b82f6', TRUE, EXTRACT(EPOCH FROM NOW()) * 1000, EXTRACT(EPOCH FROM NOW()) * 1000),
    (gen_random_uuid(), 'Research', '#22c55e', TRUE, EXTRACT(EPOCH FROM NOW()) * 1000, EXTRACT(EPOCH FROM NOW()) * 1000),
    (gen_random_uuid(), 'Design', '#ec4899', TRUE, EXTRACT(EPOCH FROM NOW()) * 1000, EXTRACT(EPOCH FROM NOW()) * 1000);
```

---

## Pydantic Models

```python
from pydantic import BaseModel, Field
from uuid import UUID

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., pattern=r'^#[0-9a-fA-F]{6}$')  # Hex color
    is_default: bool = False

class TagCreate(TagBase):
    created_at: int  # Unix timestamp (ms) - client provides
    updated_at: int  # Unix timestamp (ms) - client provides

class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=r'^#[0-9a-fA-F]{6}$')
    updated_at: int  # Unix timestamp (ms) - client provides

class Tag(TagBase):
    id: UUID
    created_at: int  # Unix timestamp (ms)
    updated_at: int  # Unix timestamp (ms)
    deleted_at: int | None = None

    class Config:
        from_attributes = True
```

---

## API Endpoints

### Base URL
```
/api/v1
```

All endpoints use **snake_case** for JSON field names to match Python conventions.

---

### `GET /tags`

List all tags, optionally filtered by update time for sync.

**Query Parameters:**
- `since` (optional): Unix timestamp (ms). Returns only tags with `updated_at > since`

**Response:** `Tag[]`

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "General",
      "color": "#14b8a6",
      "is_default": true,
      "created_at": 1704000000000,
      "updated_at": 1704000000000,
      "deleted_at": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Custom Tag",
      "color": "#f97316",
      "is_default": false,
      "created_at": 1704060000000,
      "updated_at": 1704060000000,
      "deleted_at": null
    }
  ]
}
```

**Note:** Include soft-deleted tags (where `deleted_at` is not null) in the response when `since` is provided, so clients can sync deletions.

---

### `POST /tags`

Create a new tag.

**Request Body:**
```json
{
  "name": "Urgent",
  "color": "#ef4444",
  "is_default": false,
  "created_at": 1704067200000,
  "updated_at": 1704067200000
}
```

**Response:** `201 Created`
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Urgent",
  "color": "#ef4444",
  "is_default": false,
  "created_at": 1704067200000,
  "updated_at": 1704067200000,
  "deleted_at": null
}
```

**Errors:**
- `400`: Tag name already exists
- `422`: Validation error

---

### `PATCH /tags/{id}`

Update an existing tag.

**Request Body:**
```json
{
  "name": "Updated Name",
  "color": "#ec4899",
  "is_default": false,
  "created_at": 1704067200000,
  "updated_at": 1704070000000
}
```

**Response:** `200 OK`
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Updated Name",
  "color": "#ec4899",
  "is_default": false,
  "created_at": 1704067200000,
  "updated_at": 1704070000000,
  "deleted_at": null
}
```

**Errors:**
- `404`: Tag not found
- `400`: Tag name already exists (if changing name)
- `422`: Validation error

**Note:** Default tags (`is_default: true`) can be renamed but not deleted.

---

### `DELETE /tags/{id}`

Soft-delete a tag (sets `deleted_at`).

**Response:** `204 No Content`

**Errors:**
- `404`: Tag not found
- `400`: Cannot delete default tags

**Note:** When a tag is deleted, tasks using that tag should retain the tag name string (orphaned tags are acceptable).

---

## Sync Behavior

The frontend syncs tags independently from tasks:

1. **Pull:** `GET /tags?since={lastSyncAt}` to get updated/deleted tags
2. **Push:** For each pending local tag:
   - If no `serverId`: `POST /tags`
   - If has `serverId`: `PATCH /tags/{serverId}`
   - If soft-deleted with `serverId`: `DELETE /tags/{serverId}`

### Conflict Resolution

Same as tasks: **last-write-wins** based on `updated_at` timestamp.

---

## Color Palette

The frontend auto-assigns colors from this palette for new tags:

```typescript
const TAG_COLORS = [
  '#14b8a6',  // teal
  '#a855f7',  // purple
  '#3b82f6',  // blue
  '#22c55e',  // green
  '#ec4899',  // pink
  '#f97316',  // orange
  '#ef4444',  // red
  '#eab308'   // yellow
];
```

The backend doesn't need to enforce these colors - it just stores whatever hex color the client sends.

---

## Example FastAPI Router

```python
from fastapi import APIRouter, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.schemas.tag import Tag, TagCreate, TagUpdate
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[Tag])
async def get_tags(since: Optional[int] = Query(None)):
    """Get all tags, optionally filtered by updated_at > since"""
    if since:
        return await tag_service.get_tags_since(since)
    return await tag_service.get_all_tags()


@router.post("", response_model=Tag, status_code=201)
async def create_tag(tag: TagCreate):
    """Create a new tag"""
    existing = await tag_service.get_by_name(tag.name)
    if existing and existing.deleted_at is None:
        raise HTTPException(400, f"Tag '{tag.name}' already exists")
    return await tag_service.create_tag(tag)


@router.patch("/{tag_id}", response_model=Tag)
async def update_tag(tag_id: UUID, tag: TagUpdate):
    """Update a tag"""
    existing = await tag_service.get_by_id(tag_id)
    if not existing:
        raise HTTPException(404, "Tag not found")

    if tag.name:
        name_check = await tag_service.get_by_name(tag.name)
        if name_check and name_check.id != tag_id and name_check.deleted_at is None:
            raise HTTPException(400, f"Tag '{tag.name}' already exists")

    return await tag_service.update_tag(tag_id, tag)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(tag_id: UUID):
    """Soft-delete a tag"""
    existing = await tag_service.get_by_id(tag_id)
    if not existing:
        raise HTTPException(404, "Tag not found")
    if existing.is_default:
        raise HTTPException(400, "Cannot delete default tags")

    await tag_service.soft_delete(tag_id)
```

---

## Migration Checklist

1. Create `tags` table with schema above
2. Seed default tags (General, Work, Personal, Research, Design)
3. Remove `valid_tag` constraint from `tasks` table
4. Add tag router to FastAPI app
5. Update CORS if needed (should already allow all needed origins)

---

## Testing

Test the following scenarios:

1. **Get all tags** - returns seeded defaults
2. **Create custom tag** - returns new tag with generated ID
3. **Create duplicate name** - returns 400 error
4. **Update tag name** - returns updated tag
5. **Delete custom tag** - returns 204
6. **Delete default tag** - returns 400 error
7. **Sync with `since` param** - returns only changed tags
8. **Soft-deleted tags appear in sync** - when `since` provided
