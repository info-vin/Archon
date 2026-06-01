"""Simple test configuration for Archon - Essential tests only."""

import os
import uuid
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

# Set test environment - always override to ensure test isolation
os.environ["TEST_MODE"] = "true"
os.environ["TESTING"] = "true"
# Set fake database credentials to prevent connection attempts
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
# Set required port environment variables for ServiceDiscovery
os.environ["ARCHON_SERVER_PORT"] = "8181"
os.environ["ARCHON_MCP_PORT"] = "8051"
os.environ["ARCHON_AGENTS_PORT"] = "8052"

# Global patches that need to be active during module imports and app initialization
from unittest.mock import AsyncMock

# --- START: GLOBAL LLM MOCKING DEFINITIONS ---
# Mock GenAI Response
mock_genai_response = MagicMock()
mock_genai_response.text = "Mocked GenAI Response in Traditional Chinese (繁體中文)"

# Mock GenAI Client
mock_genai_client_instance = MagicMock()
mock_genai_client_instance.models.generate_content.return_value = mock_genai_response
mock_genai_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_genai_response)

# Mock OpenAI Response
mock_openai_response = MagicMock()
mock_openai_choice = MagicMock()
mock_openai_message = MagicMock()
mock_openai_message.content = "Mocked OpenAI Response in Traditional Chinese (繁體中文)"
mock_openai_choice.message = mock_openai_message
mock_openai_response.choices = [mock_openai_choice]

# Mock OpenAI Embeddings Response
mock_embeddings_response = MagicMock()
mock_embedding_data = MagicMock()
mock_embedding_data.embedding = [0.1] * 384
mock_embeddings_response.data = [mock_embedding_data]

# Mock OpenAI Client Instances
mock_openai_client_instance = MagicMock()
mock_openai_client_instance.chat.completions.create = AsyncMock(return_value=mock_openai_response)
mock_openai_client_instance.embeddings.create = AsyncMock(return_value=mock_embeddings_response)

mock_openai_sync_client_instance = MagicMock()
mock_openai_sync_client_instance.chat.completions.create.return_value = mock_openai_response
mock_openai_sync_client_instance.embeddings.create.return_value = mock_embeddings_response

# Mock LiteLLM Response
mock_litellm_response = {
    "choices": [
        {
            "message": {
                "content": "Mocked LiteLLM Summary Response"
            }
        }
    ]
}

# Mock PydanticAI RunResult
mock_run_result = MagicMock()
mock_run_result.data = "Mocked Agent Response"
mock_run_result.output = "Mocked Agent Response"
mock_run_result.usage = MagicMock()
mock_run_result.usage.input_tokens = 10
mock_run_result.usage.output_tokens = 10
mock_run_result.model_used = "mock-model"

# --- END: GLOBAL LLM MOCKING DEFINITIONS ---

# --- START: PYTEST NETWORK & KEY BOUNDARY CHECKS ---
def check_internet_connection():
    import socket
    try:
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")

def pytest_runtest_setup(item):
    if "integration" in item.keywords:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or not check_internet_connection():
            pytest.skip("Skipping integration test: No internet or API keys found.")
# --- END: PYTEST BOUNDARY CHECKS ---

mock_client = MagicMock()
mock_table = MagicMock()
mock_select = MagicMock()
mock_execute = MagicMock()
mock_execute.data = []
mock_select.execute.return_value = mock_execute
mock_select.eq.return_value = mock_select
mock_select.order.return_value = mock_select
mock_table.select.return_value = mock_select
mock_client.table.return_value = mock_table

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# --- START: CRITICAL PATH FIX FOR PYTEST SRC-LAYOUT ---
# This ensures Python can find 'server' as a top-level module when running tests
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# --- END: CRITICAL PATH FIX ---

# Apply global patches immediately
_global_patches = [
    patch("supabase.create_client", return_value=mock_client),
    patch("server.services.client_manager.get_supabase_client", return_value=mock_client),
    patch("server.utils.get_supabase_client", return_value=mock_client),
    patch("google.genai.Client", return_value=mock_genai_client_instance),
    patch("openai.OpenAI", return_value=mock_openai_sync_client_instance),
    patch("openai.AsyncOpenAI", return_value=mock_openai_client_instance),
    patch("litellm.completion", AsyncMock(return_value=mock_litellm_response)),
    patch("pydantic_ai.Agent.run", AsyncMock(return_value=mock_run_result)),
    patch("pydantic_ai.Agent.run_sync", MagicMock(return_value=mock_run_result)),
]

print("\n--- DEBUG CONTEST.PY IMPORT ENVIRONMENT ---")
print(f"sys.path: {sys.path}")
print(f"sys.modules keys (first 20): {list(sys.modules.keys())[:20]}")
print(f"sys.modules['server']: {sys.modules.get('server')}")
print(f"sys.modules['server.services']: {sys.modules.get('server.services')}")
print("--- END DEBUG ---")

for p in _global_patches:
    p.start()


# --- START: STATEFUL MOCK SUPABASE CLIENT DEFINITION ---



class MockQueryBuilder:
    def __init__(self, data: list, table_name: str, client: 'StatefulMockSupabaseClient', action: str, action_data: any = None):
        self.data = data
        self.table_name = table_name
        self.client = client
        self.action = action
        self.action_data = action_data
        self.filters = []
        self.orders = []
        self.limit_val = None

    def eq(self, field: str, value: any):
        self.filters.append(lambda x: x.get(field) == value)
        return self

    def neq(self, field: str, value: any):
        self.filters.append(lambda x: x.get(field) != value)
        return self

    def ilike(self, field: str, pattern: str):
        clean_pat = pattern.replace("%", "").lower()
        self.filters.append(lambda x: clean_pat in str(x.get(field, "")).lower())
        return self

    def contains(self, field: str, value: any):
        def _check_contains(x):
            val = x.get(field)
            if isinstance(val, list):
                if isinstance(value, list):
                    return all(item in val for item in value)
                return value in val
            return False
        self.filters.append(_check_contains)
        return self

    def or_(self, filter_str: str):
        # Allow pass-through for test simplicity
        return self

    def order(self, field: str, desc: bool = False):
        self.orders.append((field, desc))
        return self

    def limit(self, limit_val: int):
        self.limit_val = limit_val
        return self

    def execute(self):
        target_records = self.data

        filtered_records = []
        for r in target_records:
            match = True
            for f in self.filters:
                try:
                    if not f(r):
                        match = False
                        break
                except Exception:
                    match = False
                    break
            if match:
                filtered_records.append(r)

        for field, desc in self.orders:
            try:
                filtered_records.sort(key=lambda x: x.get(field), reverse=desc)
            except Exception:
                pass

        if self.limit_val is not None:
            filtered_records = filtered_records[:self.limit_val]

        response = MagicMock()

        if self.action == 'select':
            response.data = [dict(r) for r in filtered_records]

        elif self.action == 'insert':
            inserted = []
            if isinstance(self.action_data, list):
                for item in self.action_data:
                    new_item = dict(item)
                    if "id" not in new_item:
                        new_item["id"] = str(uuid.uuid4())
                    self.data.append(new_item)
                    inserted.append(new_item)
            else:
                new_item = dict(self.action_data)
                if "id" not in new_item:
                    new_item["id"] = str(uuid.uuid4())
                self.data.append(new_item)
                inserted.append(new_item)
            response.data = inserted

        elif self.action == 'update':
            updated = []
            for r in filtered_records:
                r.update(self.action_data)
                updated.append(dict(r))
            response.data = updated

        elif self.action == 'delete':
            for r in filtered_records:
                if r in self.data:
                    self.data.remove(r)
            response.data = [dict(r) for r in filtered_records]

        return response


class MockTable:
    def __init__(self, data: list, table_name: str, client: 'StatefulMockSupabaseClient'):
        self.data = data
        self.table_name = table_name
        self.client = client

    def select(self, fields: str = "*"):
        return MockQueryBuilder(self.data, self.table_name, self.client, 'select')

    def insert(self, data: dict | list):
        return MockQueryBuilder(self.data, self.table_name, self.client, 'insert', data)

    def update(self, data: dict):
        return MockQueryBuilder(self.data, self.table_name, self.client, 'update', data)

    def delete(self):
        return MockQueryBuilder(self.data, self.table_name, self.client, 'delete')


class StatefulMockSupabaseClient:
    def __init__(self):
        self._db = {}
        self.auth = MagicMock()
        self.auth.get_user.return_value = None
        self.storage = MagicMock()

    def table(self, table_name: str):
        if table_name not in self._db:
            self._db[table_name] = []
        return MockTable(self._db[table_name], table_name, self)

# --- END: STATEFUL MOCK SUPABASE CLIENT DEFINITION ---


@pytest.fixture(autouse=True)
def ensure_test_environment():
    """Ensure test environment is properly set for each test."""
    # Force test environment settings - this runs before each test
    os.environ["TEST_MODE"] = "true"
    os.environ["TESTING"] = "true"
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
    os.environ["ARCHON_SERVER_PORT"] = "8181"
    os.environ["ARCHON_MCP_PORT"] = "8051"
    os.environ["ARCHON_AGENTS_PORT"] = "8052"
    yield


@pytest.fixture(scope="function", autouse=True)
def mock_supabase_db():
    """Shared stateful Supabase database emulator that intercepts network requests."""
    client = StatefulMockSupabaseClient()
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.route(host__regex=r".*supabase\.co").mock(
            side_effect=httpx.ConnectError("Blocked connection to Supabase during hermetic tests.")
        )
        yield client


@pytest.fixture(autouse=True)
def prevent_real_db_calls(mock_supabase_db):
    """Automatically prevent any real database calls in all tests."""
    with patch("supabase.create_client", return_value=mock_supabase_db):
        with patch("server.services.client_manager.get_supabase_client", return_value=mock_supabase_db):
            with patch("server.utils.get_supabase_client", return_value=mock_supabase_db):
                yield


@pytest.fixture
def mock_supabase_client(mock_supabase_db):
    """Mock Supabase client for testing."""
    return mock_supabase_db


@pytest.fixture
def client(mock_supabase_client):
    """FastAPI test client with mocked database."""
    # Patch all the ways Supabase client can be created
    with patch(
        "server.services.client_manager.get_supabase_client",
        return_value=mock_supabase_client,
    ):
        with patch(
            "server.utils.get_supabase_client",
            return_value=mock_supabase_client,
        ):
            with patch(
                "src.server.utils.get_supabase_client",
                return_value=mock_supabase_client,
            ):
                with patch(
                    "server.services.credential_service.create_client",
                    return_value=mock_supabase_client,
                    create=True,
                ):
                    with patch("supabase.create_client", return_value=mock_supabase_client):
                        from unittest.mock import AsyncMock

                        import server.main as server_main
                        from server.auth.dependencies import get_current_user

                    # Mark initialization as complete for testing (before accessing app)
                    server_main._initialization_complete = True
                    app = server_main.app

                    # Mock the schema check to always return valid
                    mock_schema_check = AsyncMock(return_value={"valid": True, "message": "Schema is up to date"})

                    # Global Auth Mock for tests
                    app.dependency_overrides[get_current_user] = lambda: {
                        "id": "test-admin",
                        "role": "admin",
                        "email": "admin@test.com",
                    }

                    with patch("server.main._check_database_schema", new=mock_schema_check, create=True):
                        return TestClient(app)


@pytest.fixture
def test_project():
    """Simple test project data."""
    return {"title": "Test Project", "description": "A test project for essential tests"}


@pytest.fixture
def test_task():
    """Simple test task data."""
    return {
        "title": "Test Task",
        "description": "A test task for essential tests",
        "status": "todo",
        "assignee": "User",
    }


@pytest.fixture
def test_knowledge_item():
    """Simple test knowledge item data."""
    return {
        "url": "https://example.com/test",
        "title": "Test Knowledge Item",
        "content": "This is test content for knowledge base",
        "source_id": "test-source",
    }
