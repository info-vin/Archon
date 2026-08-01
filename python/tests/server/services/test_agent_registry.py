import pytest
from unittest.mock import MagicMock, patch
from src.server.services.agent_registry import get_tool_min_level, get_agent_uuid, get_agent_config

def test_get_tool_min_level_static():
    assert get_tool_min_level("apply_modification") == 2
    assert get_tool_min_level("search_job_market") == 0
    assert get_tool_min_level("unknown_tool") == 0

@patch("src.server.services.agent_registry.get_supabase_client")
def test_get_agent_uuid_success(mock_get_supabase_client):
    mock_supabase = MagicMock()
    mock_get_supabase_client.return_value = mock_supabase

    # Mock first try success (archon_agents)
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "uuid-123"}]

    get_agent_uuid.cache_clear()
    assert get_agent_uuid("dev-bot") == "uuid-123"

@patch("src.server.services.agent_registry.get_supabase_client")
def test_get_agent_uuid_fallback_success(mock_get_supabase_client):
    mock_supabase = MagicMock()
    mock_get_supabase_client.return_value = mock_supabase

    # Mock first try fail, second try success (profiles)
    def side_effect(*args, **kwargs):
        mock = MagicMock()
        if args[0] == "archon_agents":
            mock.select.return_value.eq.return_value.execute.return_value.data = []
        elif args[0] == "profiles":
            mock.select.return_value.eq.return_value.execute.return_value.data = [{"id": "uuid-456"}]
        return mock

    mock_supabase.table.side_effect = side_effect

    get_agent_uuid.cache_clear()
    assert get_agent_uuid("supervisor") == "uuid-456"

@patch("src.server.services.agent_registry.get_supabase_client")
def test_get_agent_config_success(mock_get_supabase_client):
    mock_supabase = MagicMock()
    mock_get_supabase_client.return_value = mock_supabase

    def side_effect(*args, **kwargs):
        mock = MagicMock()
        if args[0] == "archon_agents":
            mock.select.return_value.eq.return_value.execute.return_value.data = [{"id": "uuid-1", "name": "Test Bot", "model_tier": "pro", "default_tool": "test"}]
        elif args[0] == "archon_agent_tools":
            mock.select.return_value.eq.return_value.execute.return_value.data = [{"tool_name": "tool1"}]
        return mock

    mock_supabase.table.side_effect = side_effect

    with patch("src.server.services.agent_registry.prompt_service.get_prompt", return_value="Test prompt"):
        config = get_agent_config("dev-bot")

    assert config is not None
    assert config["name"] == "Test Bot"
    assert config["model_tier"] == "pro"
    assert config["system_prompt"] == "Test prompt"
    assert config["tools"] == ["tool1"]
    assert config["default_tool"] == "test"

@patch("src.server.services.agent_registry.get_supabase_client")
def test_get_agent_config_fallback(mock_get_supabase_client):
    mock_supabase = MagicMock()
    mock_get_supabase_client.return_value = mock_supabase

    # DB fail
    mock_supabase.table.side_effect = Exception("DB error")

    config = get_agent_config("dev-bot")
    assert config is not None
    assert config["name"] == "Archon DevBot"
    assert "execute_shell_command" in config["tools"]
