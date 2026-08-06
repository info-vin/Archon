import os
import sys

# Setup path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from src.server.services.client_manager import get_supabase_client  # noqa: E402
from src.server.services.shared_constants import AgentUUIDs  # noqa: E402


def main():
    print("🔍 [Audit] Verifying Agent UUIDs against Physical Database Parity...")
    supabase = get_supabase_client()

    # Get expected UUIDs via reflection on AgentUUIDs class
    expected_uuids = {}
    for attr in dir(AgentUUIDs):
        if not attr.startswith("__") and not callable(getattr(AgentUUIDs, attr)):
            expected_uuids[attr] = getattr(AgentUUIDs, attr)

    if not expected_uuids:
        print("❌ Error: No Agent UUIDs found in shared_constants.py.")
        sys.exit(1)

    print(f"Expected Agents to verify: {len(expected_uuids)}")

    try:
        res = supabase.table("profiles").select("id, name").in_("id", list(expected_uuids.values())).execute()
        found_records = {row["id"]: row["name"] for row in res.data}
    except Exception as e:
        print(f"❌ Error connecting to database or querying profiles: {e}")
        sys.exit(1)

    missing_agents = []
    for agent_name, agent_id in expected_uuids.items():
        if agent_id not in found_records:
            missing_agents.append(f"{agent_name} ({agent_id})")
        else:
            print(f"  ✅ Found: {agent_name} -> {found_records[agent_id]}")

    if missing_agents:
        print("\n❌ TWIN MISMATCH DETECTED: The following Agent UUIDs are missing in the physical database:")
        for missing in missing_agents:
            print(f"  - {missing}")
        print("\nPlease run the rescue script (migration/0.2.3/rescue/fix_missing_agents.sql) in your Supabase dashboard.")
        sys.exit(1)

    print("\n🎉 [Audit] Physical Database Parity Confirmed. All agents are registered.")
    sys.exit(0)

if __name__ == "__main__":
    main()
