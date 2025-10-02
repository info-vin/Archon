"""
Tests for the Log API endpoint.
"""
from unittest.mock import MagicMock

# Assuming the client and mock_supabase_client fixtures are defined in conftest.py

def test_record_gemini_log_success(client, mock_supabase_client, mocker):
    """
    Tests the successful creation of a Gemini log entry.
    """
    # Arrange
    # Patch the get_supabase_client call within the service layer to return the mock
    mocker.patch('src.server.services.log_service.get_supabase_client', return_value=mock_supabase_client)

    test_payload = {
        "user_input": "SyntaxError: invalid syntax on line 5",
        "gemini_response": "It looks like you have a typo in your variable name.",
        "project_name": "Archon",
        "user_name": "test_user"
    }

    # Mock the Supabase client response for a successful insertion
    mock_insert_response = MagicMock()
    mock_insert_response.data = [{'id': '12345', **test_payload}]

    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

    # Act
    response = client.post("/api/record-gemini-log", json=test_payload)

    # Assert
    assert response.status_code == 201
    json_response = response.json()
    assert json_response["message"] == "Log recorded successfully"
    assert json_response["log_id"] == '12345'

    # Verify that the insert method was called with the correct data
    called_with_data = mock_supabase_client.table.return_value.insert.call_args[0][0]
    assert called_with_data["gemini_response"] == test_payload["gemini_response"]
    assert called_with_data["user_input"] == test_payload["user_input"]


def test_record_gemini_log_missing_required_field(client):
    """
    Tests that a request fails if the required 'gemini_response' field is missing.
    """
    # Arrange
    test_payload = {
        "user_input": "Some input",
        "project_name": "Archon"
        # gemini_response is missing
    }

    # Act
    response = client.post("/api/record-gemini-log", json=test_payload)

    # Assert
    assert response.status_code == 422  # Unprocessable Entity


def test_record_gemini_log_database_error(client, mock_supabase_client, mocker):
    """
    Tests the API's response to a database insertion failure.
    """
    # Arrange
    # Patch the get_supabase_client call to ensure the mock is used
    mocker.patch('src.server.services.log_service.get_supabase_client', return_value=mock_supabase_client)

    test_payload = {
        "user_input": "Another error",
        "gemini_response": "A valid response.",
        "project_name": "Archon"
    }

    # Mock the Supabase client to simulate a failure (e.g., by returning no data)
    mock_failure_response = MagicMock()
    mock_failure_response.data = None
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_failure_response

    # Act
    response = client.post("/api/record-gemini-log", json=test_payload)

    # Assert
    assert response.status_code == 500
    json_response = response.json()
    assert "Failed to insert log into database" in json_response["detail"]
