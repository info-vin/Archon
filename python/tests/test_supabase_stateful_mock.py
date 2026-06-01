"""
Tests for stateful database emulation and network blocking.
"""


import httpx
import pytest


@pytest.mark.asyncio
async def test_stateful_crud_operations(mock_supabase_client):
    """Test that the stateful emulator retains values on insert, update, select, and delete."""
    client = mock_supabase_client

    # 1. Select initially empty
    res = client.table("projects").select("*").execute()
    assert len(res.data) == 0

    # 2. Insert records
    inserted = client.table("projects").insert([
        {"title": "Project A", "status": "active"},
        {"title": "Project B", "status": "archived"}
    ]).execute()

    assert len(inserted.data) == 2
    assert inserted.data[0]["title"] == "Project A"
    assert "id" in inserted.data[0]

    # 3. Read back records (Read-After-Write)
    selected = client.table("projects").select("*").execute()
    assert len(selected.data) == 2

    # 4. Filter records using eq
    filtered = client.table("projects").select("*").eq("title", "Project A").execute()
    assert len(filtered.data) == 1
    assert filtered.data[0]["title"] == "Project A"

    # 5. Update record
    updated = client.table("projects").update({"status": "completed"}).eq("title", "Project A").execute()
    assert len(updated.data) == 1
    assert updated.data[0]["status"] == "completed"

    # Verify update persisted
    verify = client.table("projects").select("*").eq("title", "Project A").execute()
    assert verify.data[0]["status"] == "completed"

    # 6. Delete record
    client.table("projects").delete().eq("title", "Project B").execute()

    # Verify deletion
    remaining = client.table("projects").select("*").execute()
    assert len(remaining.data) == 1
    assert remaining.data[0]["title"] == "Project A"


@pytest.mark.asyncio
async def test_respx_network_blocking():
    """Test that any real HTTPX network calls to supabase.co are blocked by respx."""
    # We attempt a real network connection to supabase.co using httpx
    # Under standard environment, this would hit the network. With respx, it should be intercepted.
    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.ConnectError) as exc_info:
            await client.get("https://xyz.supabase.co/rest/v1/projects")

        assert "Blocked connection to Supabase" in str(exc_info.value)
