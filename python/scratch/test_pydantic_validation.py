
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.server.schemas.agent_outputs import AgentOutputSchema


def test_validation():
    # 1. Test Text Output
    text_out = AgentOutputSchema(
        agent_id="f0f00000-0000-0000-0000-000000000001",
        output="Hello world"
    )
    print(f"Text Output Validated: {text_out.model_dump(mode='json')}")

    # 2. Test Group Chat Output
    chat_content = {
        "summary": "Meeting concluded",
        "decisions": ["Launch project"],
        "next_steps": ["Hire team"],
        "raw_responses": {"worker-1": "Agreed"}
    }

    chat_out = AgentOutputSchema(
        agent_id="f0f00000-0000-0000-0000-000000000001",
        output_type="group_chat",
        output=chat_content
    )
    print(f"Chat Output Validated: {chat_out.model_dump(mode='json')}")

    # 3. Test Validation Error
    try:
        AgentOutputSchema(agent_id="invalid", output=123)
    except Exception as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    test_validation()
