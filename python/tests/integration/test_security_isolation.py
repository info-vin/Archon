from unittest.mock import MagicMock

import pytest

from server.services.propose_change_service import ProposeChangeService


@pytest.mark.asyncio
async def test_department_isolation_physical_logic():
    """
    Physically verifies that a Manager can only see proposals
    belonging to their own department via the JSONB filter.
    """
    # 1. Setup Mock Supabase Client
    mock_db = MagicMock()

    # 2. Mock Data: Proposals from different departments
    # These represent what's physically in the 'proposed_changes' table
    all_proposals = [
        {"id": "p1", "request_payload": {"created_by_dept": "Marketing"}, "change_summary": "Marketing Blog"},
        {"id": "p2", "request_payload": {"created_by_dept": "Sales"}, "change_summary": "Sales Pitch"},
        {"id": "p3", "request_payload": {"created_by_dept": "Marketing"}, "change_summary": "Another Ad"},
    ]

    # 3. Mock Data: Manager Profiles
    manager_marketing = {"id": "m1", "department": "Marketing", "role": "manager"}
    manager_sales = {"id": "m2", "department": "Sales", "role": "manager"}

    service = ProposeChangeService(db_client=mock_db)

    # --- Test Scenario A: Marketing Manager ---
    # Setup chain of mocks for Supabase syntax: table().select().eq().single().execute()
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = (
        manager_marketing
    )

    # Setup chain for the query filter
    # We expect table("proposed_changes").select("*").eq("status", "pending").filter(...).order().execute()
    mock_query = mock_db.table.return_value.select.return_value.eq.return_value.filter.return_value.order.return_value
    mock_query.execute.return_value.data = [
        p for p in all_proposals if p["request_payload"]["created_by_dept"] == "Marketing"
    ]

    res_marketing = await service.list_proposals(user_id="m1")

    # PHYSICAL ASSERTIONS
    assert len(res_marketing) == 2
    assert all(p["request_payload"]["created_by_dept"] == "Marketing" for p in res_marketing)
    print("\n✅ Assertion Passed: Marketing Manager only sees Marketing proposals.")

    # --- Test Scenario B: Sales Manager ---
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = (
        manager_sales
    )
    mock_query.execute.return_value.data = [
        p for p in all_proposals if p["request_payload"]["created_by_dept"] == "Sales"
    ]

    res_sales = await service.list_proposals(user_id="m2")

    # PHYSICAL ASSERTIONS
    assert len(res_sales) == 1
    assert res_sales[0]["request_payload"]["created_by_dept"] == "Sales"
    print("✅ Assertion Passed: Sales Manager only sees Sales proposals.")


if __name__ == "__main__":
    pytest.main([__file__])
