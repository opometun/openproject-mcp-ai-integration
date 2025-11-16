"""
Unit tests for work package tools.

Tests the add_comment tool and placeholders for unimplemented tools.
Uses respx for HTTP mocking to avoid real API calls.
"""

import pytest
import respx
import httpx
import json
from urllib.parse import unquote
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from openproject_mcp.tools import work_packages

from tests.helpers.mocks import mock_activity

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def server(mock_settings):
    """FastMCP server with work package tools registered."""
    server = FastMCP("test-openproject")
    work_packages.register(server, mock_settings)
    return server


@pytest.fixture
def base_url(mock_settings):
    """Base URL for API endpoints (matching what OpenProjectClient uses)."""
    return str(mock_settings.url).rstrip("/") + "/api/v3"


# ============================================================================
# Test: create_work_package
# ============================================================================


class TestCreateWorkPackage:
    """Test suite for create_work_package tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_minimal(self, server, base_url):
        """Test creating a work package with minimal required fields."""
        import json

        expected_response = {
            "id": 123,
            "subject": "New Task",
            "_links": {
                "self": {"href": "/api/v3/work_packages/123"},
                "project": {"href": "/api/v3/projects/1"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {"params": {"project_id": 1, "subject": "New Task"}},
        )

        assert route.called, "API endpoint was not called"
        
        # Verify the request payload
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["subject"] == "New Task"
        assert request_body["_links"]["project"]["href"] == "/api/v3/projects/1"
        
        # Verify the response
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 123
        assert response_data["subject"] == "New Task"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_type(self, server, base_url):
        """Test creating a work package with a specific type."""
        import json

        expected_response = {
            "id": 124,
            "subject": "Bug Report",
            "_links": {
                "self": {"href": "/api/v3/work_packages/124"},
                "project": {"href": "/api/v3/projects/1"},
                "type": {"href": "/api/v3/types/2"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {"params": {"project_id": 1, "subject": "Bug Report", "type_id": 2}},
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["_links"]["type"]["href"] == "/api/v3/types/2"
        
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 124

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_dates(self, server, base_url):
        """Test creating a work package with start and due dates."""
        import json

        expected_response = {
            "id": 125,
            "subject": "Task with Dates",
            "startDate": "2024-01-15",
            "dueDate": "2024-01-31",
            "_links": {
                "self": {"href": "/api/v3/work_packages/125"},
                "project": {"href": "/api/v3/projects/1"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "Task with Dates",
                    "start_date": "2024-01-15",
                    "due_date": "2024-01-31",
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["startDate"] == "2024-01-15"
        assert request_body["dueDate"] == "2024-01-31"
        
        response_data = json.loads(result[0].text)
        assert response_data["startDate"] == "2024-01-15"
        assert response_data["dueDate"] == "2024-01-31"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_description(self, server, base_url):
        """Test creating a work package with markdown description."""
        import json

        markdown_desc = "# Description\n\nThis is a **test** description."
        expected_response = {
            "id": 126,
            "subject": "Task with Description",
            "description": {"raw": markdown_desc},
            "_links": {
                "self": {"href": "/api/v3/work_packages/126"},
                "project": {"href": "/api/v3/projects/1"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "Task with Description",
                    "description": markdown_desc,
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["description"]["raw"] == markdown_desc
        
        response_data = json.loads(result[0].text)
        assert response_data["description"]["raw"] == markdown_desc

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_assignee(self, server, base_url):
        """Test creating a work package with an assignee."""
        import json

        expected_response = {
            "id": 127,
            "subject": "Assigned Task",
            "_links": {
                "self": {"href": "/api/v3/work_packages/127"},
                "project": {"href": "/api/v3/projects/1"},
                "assignee": {"href": "/api/v3/users/5"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "Assigned Task",
                    "assignee_id": 5,
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["_links"]["assignee"]["href"] == "/api/v3/users/5"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_priority(self, server, base_url):
        """Test creating a work package with priority."""
        import json

        expected_response = {
            "id": 128,
            "subject": "High Priority Task",
            "_links": {
                "self": {"href": "/api/v3/work_packages/128"},
                "project": {"href": "/api/v3/projects/1"},
                "priority": {"href": "/api/v3/priorities/3"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "High Priority Task",
                    "priority_id": 3,
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["_links"]["priority"]["href"] == "/api/v3/priorities/3"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_with_estimated_time(self, server, base_url):
        """Test creating a work package with estimated time."""
        import json

        expected_response = {
            "id": 129,
            "subject": "Task with Time Estimate",
            "estimatedTime": "PT8H",
            "_links": {
                "self": {"href": "/api/v3/work_packages/129"},
                "project": {"href": "/api/v3/projects/1"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "Task with Time Estimate",
                    "estimated_time": "PT8H",
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["estimatedTime"] == "PT8H"
        
        response_data = json.loads(result[0].text)
        assert response_data["estimatedTime"] == "PT8H"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_full_options(self, server, base_url):
        """Test creating a work package with all optional fields."""
        import json

        expected_response = {
            "id": 130,
            "subject": "Complete Task",
            "description": {"raw": "Full description"},
            "startDate": "2024-02-01",
            "dueDate": "2024-02-15",
            "estimatedTime": "PT16H",
            "_links": {
                "self": {"href": "/api/v3/work_packages/130"},
                "project": {"href": "/api/v3/projects/1"},
                "type": {"href": "/api/v3/types/1"},
                "status": {"href": "/api/v3/statuses/2"},
                "assignee": {"href": "/api/v3/users/3"},
                "priority": {"href": "/api/v3/priorities/2"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {
                "params": {
                    "project_id": 1,
                    "subject": "Complete Task",
                    "type_id": 1,
                    "status_id": 2,
                    "description": "Full description",
                    "assignee_id": 3,
                    "start_date": "2024-02-01",
                    "due_date": "2024-02-15",
                    "estimated_time": "PT16H",
                    "priority_id": 2,
                }
            },
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["subject"] == "Complete Task"
        assert request_body["description"]["raw"] == "Full description"
        assert request_body["startDate"] == "2024-02-01"
        assert request_body["dueDate"] == "2024-02-15"
        assert request_body["estimatedTime"] == "PT16H"
        assert request_body["_links"]["type"]["href"] == "/api/v3/types/1"
        assert request_body["_links"]["status"]["href"] == "/api/v3/statuses/2"
        assert request_body["_links"]["assignee"]["href"] == "/api/v3/users/3"
        assert request_body["_links"]["priority"]["href"] == "/api/v3/priorities/2"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_project_not_found(self, server, base_url):
        """Test error handling when project doesn't exist."""
        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(404, json={"message": "Project not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 99999, "subject": "Test"}},
            )

        assert route.called
        assert "Resource not found" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 1, "subject": "Test"}},
            )

        assert route.called
        assert "Authentication failed" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_forbidden(self, server, base_url):
        """Test error handling when user lacks permission."""
        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(403, json={"message": "Forbidden"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 1, "subject": "Test"}},
            )

        assert route.called
        assert "Permission denied" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_validation_error(self, server, base_url):
        """Test error handling for invalid data."""
        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(
                422, json={"message": "Subject cannot be empty"}
            )
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 1, "subject": "Test"}},
            )

        assert route.called
        assert "Validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_work_package_invalid_project_id(self, server):
        """Test validation error for invalid project ID."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": -1, "subject": "Test"}},
            )

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_work_package_empty_subject(self, server):
        """Test validation error for empty subject."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 1, "subject": ""}},
            )

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_work_package_missing_required_params(self, server):
        """Test validation error when required parameters are missing."""
        with pytest.raises(ToolError):
            await server.call_tool(
                "create_work_package",
                {"params": {"project_id": 1}},  # Missing 'subject'
            )

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_work_package_unicode_subject(self, server, base_url):
        """Test creating a work package with unicode characters in subject."""
        import json

        unicode_subject = "Task 世界 🌍 Привет"
        expected_response = {
            "id": 131,
            "subject": unicode_subject,
            "_links": {
                "self": {"href": "/api/v3/work_packages/131"},
                "project": {"href": "/api/v3/projects/1"},
            },
        }

        route = respx.post(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(201, json=expected_response)
        )

        result = await server.call_tool(
            "create_work_package",
            {"params": {"project_id": 1, "subject": unicode_subject}},
        )

        assert route.called
        request_body = json.loads(route.calls.last.request.content)
        assert request_body["subject"] == unicode_subject


# ============================================================================
# Test: add_comment
# ============================================================================


class TestAddComment:
    """Test suite for add_comment tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_success(self, server, base_url):
        """Test successful comment addition returns activity data."""
        import json

        expected_response = mock_activity(456, "Test comment")

        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        result = await server.call_tool(
            "add_comment",
            {"params": {"id": 123, "comment": "Test comment", "notify": False}},
        )

        assert route.called, "API endpoint was not called"

        # FastMCP returns list[TextContent], extract the actual response
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Result should not be empty"

        # FastMCP wraps dict responses in TextContent objects
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 456, "Activity ID mismatch"
        assert response_data["comment"]["raw"] == "Test comment"

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_with_notify(self, server, base_url):
        """Test comment addition with email notifications enabled."""
        import json

        expected_response = mock_activity(789, "Important update")

        route = respx.post(
            f"{base_url}/work_packages/456/activities", params={"notify": "true"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        result = await server.call_tool(
            "add_comment",
            {"params": {"id": 456, "comment": "Important update", "notify": True}},
        )

        assert route.called, "API endpoint was not called"
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 789
        assert response_data["comment"]["raw"] == "Important update"

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_markdown_formatting(self, server, base_url):
        """Test comment with markdown formatting is preserved."""
        import json

        markdown_text = "# Header\n\n- Item 1\n- Item 2\n\n**Bold text**"
        expected_response = mock_activity(999, markdown_text)

        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        result = await server.call_tool(
            "add_comment",
            {"params": {"id": 123, "comment": markdown_text, "notify": False}},
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["comment"]["raw"] == markdown_text

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_work_package_not_found(self, server, base_url):
        """Test error handling when work package doesn't exist."""
        route = respx.post(
            f"{base_url}/work_packages/99999/activities", params={"notify": "false"}
        ).mock(
            return_value=httpx.Response(404, json={"message": "Work package not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment",
                {"params": {"id": 99999, "comment": "Test", "notify": False}},
            )

        assert route.called
        assert "Resource not found" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(401, json={"message": "Unauthorized"}))

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment",
                {"params": {"id": 123, "comment": "Test", "notify": False}},
            )

        assert route.called
        assert "Authentication failed" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_forbidden(self, server, base_url):
        """Test error handling when user lacks permission."""
        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(403, json={"message": "Forbidden"}))

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment",
                {"params": {"id": 123, "comment": "Test", "notify": False}},
            )

        assert route.called
        assert "Permission denied" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_validation_error(self, server, base_url):
        """Test error handling for invalid comment data."""
        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(
            return_value=httpx.Response(
                422, json={"message": "Comment cannot be empty"}
            )
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment",
                {"params": {"id": 123, "comment": "Test", "notify": False}},
            )

        assert route.called
        assert "Validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_comment_invalid_id_negative(self, server):
        """Test validation error for negative work package ID."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment",
                {"params": {"id": -1, "comment": "Test", "notify": False}},
            )

        # Pydantic validation should catch this before making the request
        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_add_comment_invalid_id_zero(self, server):
        """Test validation error for zero work package ID."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment", {"params": {"id": 0, "comment": "Test", "notify": False}}
            )

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_add_comment_empty_comment(self, server):
        """Test validation error for empty comment text."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "add_comment", {"params": {"id": 123, "comment": "", "notify": False}}
            )

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_add_comment_missing_required_params(self, server):
        """Test validation error when required parameters are missing."""
        with pytest.raises(ToolError):
            await server.call_tool(
                "add_comment",
                {"params": {"id": 123}},  # Missing 'comment'
            )

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_default_notify_false(self, server, base_url):
        """Test that notify defaults to false when not specified."""
        import json

        expected_response = mock_activity(111, "Test")

        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        # Don't specify notify parameter
        result = await server.call_tool(
            "add_comment", {"params": {"id": 123, "comment": "Test"}}
        )

        assert route.called, "Should default to notify=false"
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 111

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_server_error_retry(self, server, base_url):
        """Test that server errors are retried according to settings."""
        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(
            side_effect=[
                httpx.Response(500, json={"message": "Internal Server Error"}),
                httpx.Response(500, json={"message": "Internal Server Error"}),
                httpx.Response(500, json={"message": "Internal Server Error"}),
            ]
        )

        with pytest.raises(ToolError):
            await server.call_tool(
                "add_comment",
                {"params": {"id": 123, "comment": "Test", "notify": False}},
            )

        # Should retry up to max_retries (3 times in mock_settings)
        assert route.call_count == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_unicode_content(self, server, base_url):
        """Test comment with unicode characters."""
        import json

        unicode_text = "Hello 世界 🌍 Привет مرحبا"
        expected_response = mock_activity(777, unicode_text)

        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        result = await server.call_tool(
            "add_comment",
            {"params": {"id": 123, "comment": unicode_text, "notify": False}},
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["comment"]["raw"] == unicode_text

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_comment_long_text(self, server, base_url):
        """Test comment with very long text."""
        import json

        long_text = "A" * 5000  # 5000 characters
        expected_response = mock_activity(888, long_text)

        route = respx.post(
            f"{base_url}/work_packages/123/activities", params={"notify": "false"}
        ).mock(return_value=httpx.Response(201, json=expected_response))

        result = await server.call_tool(
            "add_comment",
            {"params": {"id": 123, "comment": long_text, "notify": False}},
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert len(response_data["comment"]["raw"]) == 5000


class TestSearchContent:
    """Test suite for search_content tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_work_packages_only(self, server, base_url):
        """Test searching work packages only."""
        expected_response = {
            "_type": "Collection",
            "count": 2,
            "total": 2,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP 1",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                    {
                        "id": 2,
                        "subject": "Test WP 2",
                        "_links": {"self": {"href": "/api/v3/work_packages/2"}},
                    },
                ]
            },
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "search_content",
            {
                "params": {
                    "query": "test",
                    "scope": "work_packages",
                    "limit": 100,
                    "include_attachments": False,
                }
            },
        )

        assert route.called
        # Verify the request had correct filters
        assert route.calls.last.request.url.params.get("filters")
        filters_json = unquote(route.calls.last.request.url.params["filters"])
        filters = json.loads(filters_json)
        assert filters[0]["subjectOrId"]["operator"] == "**"
        assert filters[0]["subjectOrId"]["values"] == ["test"]

        response_data = json.loads(result[0].text)
        assert response_data["_type"] == "Collection"
        assert response_data["count"] == 2
        assert len(response_data["_embedded"]["elements"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_projects_only(self, server, base_url):
        """Test searching projects only."""
        expected_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {"id": 1, "identifier": "test-proj", "name": "Test Project"},
                ]
            },
        }

        route = respx.get(f"{base_url}/projects").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "search_content",
            {"params": {"query": "test", "scope": "projects", "limit": 100}},
        )

        assert route.called
        # Verify the request had correct filters
        filters_json = unquote(route.calls.last.request.url.params["filters"])
        filters = json.loads(filters_json)
        assert filters[0]["name_and_identifier"]["operator"] == "~"
        assert filters[0]["name_and_identifier"]["values"] == ["test"]

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 1
        assert response_data["_embedded"]["elements"][0]["identifier"] == "test-proj"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_both_scopes(self, server, base_url):
        """Test searching both work packages and projects."""
        wp_response = {
            "_type": "Collection",
            "count": 2,
            "total": 2,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP 1",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                    {
                        "id": 2,
                        "subject": "Test WP 2",
                        "_links": {"self": {"href": "/api/v3/work_packages/2"}},
                    },
                ]
            },
        }

        proj_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {"id": 1, "identifier": "test-proj", "name": "Test Project"},
                ]
            },
        }

        wp_route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=wp_response)
        )

        proj_route = respx.get(f"{base_url}/projects").mock(
            return_value=httpx.Response(200, json=proj_response)
        )

        result = await server.call_tool(
            "search_content",
            {"params": {"query": "test", "limit": 100}},  # No scope = both
        )

        assert wp_route.called
        assert proj_route.called

        response_data = json.loads(result[0].text)
        assert "work_packages" in response_data
        assert "projects" in response_data
        assert response_data["work_packages"]["count"] == 2
        assert response_data["projects"]["count"] == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_with_attachments(self, server, base_url):
        """Test searching work packages with attachment content/filenames."""
        text_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP 1",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                ]
            },
        }

        attachment_content_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 2,
                        "subject": "WP with attachment",
                        "_links": {"self": {"href": "/api/v3/work_packages/2"}},
                    },
                ]
            },
        }

        attachment_name_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 3,
                        "subject": "WP with file",
                        "_links": {"self": {"href": "/api/v3/work_packages/3"}},
                    },
                ]
            },
        }

        # Mock all three types of searches
        def mock_response(request):
            filters_param = request.url.params.get("filters", "")
            filters_decoded = unquote(filters_param)

            if "subjectOrId" in filters_decoded:
                return httpx.Response(200, json=text_response)
            elif "attachment_content" in filters_decoded:
                return httpx.Response(200, json=attachment_content_response)
            elif "attachment_file_name" in filters_decoded:
                return httpx.Response(200, json=attachment_name_response)
            else:
                return httpx.Response(404, json={"message": "Not found"})

        respx.get(f"{base_url}/work_packages").mock(side_effect=mock_response)

        result = await server.call_tool(
            "search_content",
            {
                "params": {
                    "query": "test",
                    "scope": "work_packages",
                    "include_attachments": True,
                }
            },
        )

        response_data = json.loads(result[0].text)
        # Should merge and deduplicate results from all three queries
        assert (
            response_data["count"] == 3
        )  # 1 from text + 1 from content + 1 from filename
        assert len(response_data["_embedded"]["elements"]) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_attachment_deduplication(self, server, base_url):
        """Test that duplicate WPs from different attachment searches are deduplicated."""
        text_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                ]
            },
        }

        # Same WP (id=1) returned from attachment search
        attachment_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                ]
            },
        }

        def mock_response(request):
            filters_param = request.url.params.get("filters", "")
            filters_decoded = unquote(filters_param)

            if "subjectOrId" in filters_decoded:
                return httpx.Response(200, json=text_response)
            else:
                # Both attachment filters return the same WP
                return httpx.Response(200, json=attachment_response)

        respx.get(f"{base_url}/work_packages").mock(side_effect=mock_response)

        result = await server.call_tool(
            "search_content",
            {
                "params": {
                    "query": "test",
                    "scope": "work_packages",
                    "include_attachments": True,
                }
            },
        )

        response_data = json.loads(result[0].text)
        # Should deduplicate - only 1 WP even though returned from multiple searches
        assert response_data["count"] == 1
        assert len(response_data["_embedded"]["elements"]) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_attachment_unsupported_graceful_fallback(
        self, server, base_url
    ):
        """Test graceful handling when attachment filters are not supported."""
        text_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Test WP",
                        "_links": {"self": {"href": "/api/v3/work_packages/1"}},
                    },
                ]
            },
        }

        def mock_response(request):
            filters_param = request.url.params.get("filters", "")
            filters_decoded = unquote(filters_param)

            if "subjectOrId" in filters_decoded:
                return httpx.Response(200, json=text_response)
            else:
                # Attachment filters not supported
                return httpx.Response(400, json={"message": "Filter not supported"})

        respx.get(f"{base_url}/work_packages").mock(side_effect=mock_response)

        result = await server.call_tool(
            "search_content",
            {
                "params": {
                    "query": "test",
                    "scope": "work_packages",
                    "include_attachments": True,
                }
            },
        )

        response_data = json.loads(result[0].text)
        # Should still return text search results even if attachment search fails
        assert response_data["count"] == 1
        assert response_data["_embedded"]["elements"][0]["id"] == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_empty_query(self, server, base_url):
        """Test search with empty query returns empty collection."""
        result = await server.call_tool(
            "search_content",
            {"params": {"query": "", "scope": "work_packages"}},
        )

        response_data = json.loads(result[0].text)
        assert response_data["_type"] == "Collection"
        assert response_data["count"] == 0
        assert response_data["total"] == 0
        assert response_data["_embedded"]["elements"] == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_empty_query_both_scopes(self, server, base_url):
        """Test search with empty query and no scope returns empty collections."""
        result = await server.call_tool(
            "search_content",
            {"params": {"query": "   "}},  # Whitespace only
        )

        response_data = json.loads(result[0].text)
        assert "work_packages" in response_data
        assert "projects" in response_data
        assert response_data["work_packages"]["count"] == 0
        assert response_data["projects"]["count"] == 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_no_results(self, server, base_url):
        """Test search that returns no results."""
        empty_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=empty_response)
        )

        result = await server.call_tool(
            "search_content",
            {"params": {"query": "nonexistent", "scope": "work_packages"}},
        )

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 0
        assert len(response_data["_embedded"]["elements"]) == 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_custom_limit(self, server, base_url):
        """Test search with custom result limit."""
        expected_response = {
            "_type": "Collection",
            "count": 5,
            "total": 5,
            "_embedded": {
                "elements": [{"id": i, "subject": f"WP {i}"} for i in range(1, 6)]
            },
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "search_content",
            {"params": {"query": "test", "scope": "work_packages", "limit": 5}},
        )

        assert route.called
        # Verify pageSize parameter
        assert route.calls.last.request.url.params.get("pageSize") == "5"

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 5

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_url_encoding(self, server, base_url):
        """Test that special characters in query are properly URL encoded."""
        expected_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        special_query = "test & value = foo"
        await server.call_tool(
            "search_content",
            {"params": {"query": special_query, "scope": "work_packages"}},
        )

        assert route.called
        # Verify the filter contains the special characters
        filters_json = unquote(route.calls.last.request.url.params["filters"])
        filters = json.loads(filters_json)
        assert filters[0]["subjectOrId"]["values"][0] == special_query

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_project_sort_by_typeahead(self, server, base_url):
        """Test that project search uses typeahead sorting."""
        expected_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [{"id": 1, "identifier": "test", "name": "Test"}]
            },
        }

        route = respx.get(f"{base_url}/projects").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        await server.call_tool(
            "search_content",
            {"params": {"query": "test", "scope": "projects"}},
        )

        assert route.called
        # Verify sortBy parameter
        sortby_json = unquote(route.calls.last.request.url.params["sortBy"])
        sortby = json.loads(sortby_json)
        assert sortby == [["typeahead", "asc"]]

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_select_fields(self, server, base_url):
        """Test that search requests include proper field selection."""
        expected_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        await server.call_tool(
            "search_content",
            {"params": {"query": "test", "scope": "work_packages"}},
        )

        assert route.called
        # Verify select parameter includes required fields
        select_param = route.calls.last.request.url.params.get("select")
        assert "total" in select_param
        assert "elements/id" in select_param
        assert "elements/subject" in select_param

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_concurrent_execution(self, server, base_url):
        """Test that searching both scopes executes concurrently."""
        import time

        call_times = []

        def track_call(response):
            call_times.append(time.time())
            return response

        wp_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {"elements": [{"id": 1, "subject": "WP"}]},
        }

        proj_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {"elements": [{"id": 1, "name": "Proj"}]},
        }

        respx.get(f"{base_url}/work_packages").mock(
            side_effect=lambda req: track_call(httpx.Response(200, json=wp_response))
        )

        respx.get(f"{base_url}/projects").mock(
            side_effect=lambda req: track_call(httpx.Response(200, json=proj_response))
        )

        await server.call_tool(
            "search_content",
            {"params": {"query": "test"}},  # No scope = both, should be concurrent
        )

        # Both endpoints should be called
        assert len(call_times) == 2
        # Calls should be close together (concurrent, not sequential)
        # Allow 100ms tolerance for test execution overhead
        assert abs(call_times[1] - call_times[0]) < 0.1

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "search_content",
                {"params": {"query": "test", "scope": "work_packages"}},
            )

        assert "Authentication failed" in str(exc_info.value)


# ============================================================================
# Test: get_work_package_statuses
# ============================================================================


class TestGetWorkPackageStatuses:
    """Test suite for get_work_package_statuses tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_statuses_success(self, server, base_url):
        """Test successful retrieval of all statuses."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 3,
            "total": 3,
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "New", "isClosed": False, "isDefault": True},
                    {
                        "id": 2,
                        "name": "In Progress",
                        "isClosed": False,
                        "isDefault": False,
                    },
                    {"id": 3, "name": "Closed", "isClosed": True, "isDefault": False},
                ]
            },
        }

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool("get_work_package_statuses", {"params": {}})

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 3
        assert len(response_data["_embedded"]["elements"]) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_statuses_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool("get_work_package_statuses", {"params": {}})

        assert route.called
        assert "Authentication failed" in str(exc_info.value)


# ============================================================================
# Test: get_work_package_types
# ============================================================================


class TestGetWorkPackageTypes:
    """Test suite for get_work_package_types tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_types_all(self, server, base_url):
        """Test retrieval of all types without project filter."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 3,
            "total": 3,
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Task", "isMilestone": False, "isDefault": True},
                    {"id": 2, "name": "Bug", "isMilestone": False, "isDefault": False},
                    {
                        "id": 3,
                        "name": "Milestone",
                        "isMilestone": True,
                        "isDefault": False,
                    },
                ]
            },
        }

        route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool("get_work_package_types", {"params": {}})

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_types_by_project(self, server, base_url):
        """Test retrieval of types filtered by project."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 2,
            "total": 2,
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Task", "isMilestone": False},
                    {"id": 2, "name": "Bug", "isMilestone": False},
                ]
            },
        }

        route = respx.get(f"{base_url}/projects/123/types").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "get_work_package_types", {"params": {"project_id": 123}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 2


# ============================================================================
# Test: resolve_status
# ============================================================================


class TestResolveStatus:
    """Test suite for resolve_status tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_status_exact_match(self, server, base_url):
        """Test exact status name match."""
        import json

        statuses_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "New", "isClosed": False, "isDefault": True},
                    {
                        "id": 2,
                        "name": "In Progress",
                        "isClosed": False,
                        "isDefault": False,
                    },
                ]
            }
        }

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=statuses_response)
        )

        result = await server.call_tool(
            "resolve_status", {"params": {"name": "In Progress"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 2
        assert response_data["name"] == "In Progress"
        assert response_data["isClosed"] is False

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_status_case_insensitive(self, server, base_url):
        """Test case-insensitive matching."""
        import json

        statuses_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "New", "isClosed": False, "isDefault": True},
                ]
            }
        }

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=statuses_response)
        )

        result = await server.call_tool("resolve_status", {"params": {"name": "new"}})

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 1
        assert response_data["name"] == "New"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_status_partial_match(self, server, base_url):
        """Test partial name matching."""
        import json

        statuses_response = {
            "_embedded": {
                "elements": [
                    {
                        "id": 2,
                        "name": "In Progress",
                        "isClosed": False,
                        "isDefault": False,
                    },
                ]
            }
        }

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=statuses_response)
        )

        result = await server.call_tool(
            "resolve_status", {"params": {"name": "Progress"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_status_disambiguation(self, server, base_url):
        """Test disambiguation when multiple matches found."""
        import json

        statuses_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Closed", "isClosed": True, "isDefault": False},
                    {
                        "id": 2,
                        "name": "Closed",
                        "isClosed": True,
                        "isDefault": False,
                    },  # Duplicate name
                ]
            }
        }

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=statuses_response)
        )

        result = await server.call_tool(
            "resolve_status", {"params": {"name": "Closed"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["disambiguation_needed"] is True
        assert len(response_data["matches"]) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_status_not_found(self, server, base_url):
        """Test error when status not found."""
        import json

        statuses_response = {"_embedded": {"elements": []}}

        route = respx.get(f"{base_url}/statuses").mock(
            return_value=httpx.Response(200, json=statuses_response)
        )

        result = await server.call_tool(
            "resolve_status", {"params": {"name": "NonExistent"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert "error" in response_data


# ============================================================================
# Test: resolve_type
# ============================================================================


class TestResolveType:
    """Test suite for resolve_type tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_type_exact_match(self, server, base_url):
        """Test exact type name match in project context."""
        import json

        types_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Task", "isMilestone": False, "isDefault": True},
                    {"id": 2, "name": "Bug", "isMilestone": False, "isDefault": False},
                ]
            }
        }

        route = respx.get(f"{base_url}/projects/123/types").mock(
            return_value=httpx.Response(200, json=types_response)
        )

        result = await server.call_tool(
            "resolve_type", {"params": {"project_id": 123, "name": "Bug"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 2
        assert response_data["name"] == "Bug"
        assert response_data["available_in_project"] is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_type_case_insensitive(self, server, base_url):
        """Test case-insensitive type matching."""
        import json

        types_response = {
            "_embedded": {
                "elements": [
                    {"id": 1, "name": "Task", "isMilestone": False, "isDefault": True},
                ]
            }
        }

        route = respx.get(f"{base_url}/projects/123/types").mock(
            return_value=httpx.Response(200, json=types_response)
        )

        result = await server.call_tool(
            "resolve_type", {"params": {"project_id": 123, "name": "task"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["id"] == 1
        assert response_data["name"] == "Task"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_type_not_in_project(self, server, base_url):
        """Test type exists globally but not in project."""
        import json

        project_types_response = {"_embedded": {"elements": []}}

        global_types_response = {
            "_embedded": {
                "elements": [
                    {"id": 5, "name": "Epic", "isMilestone": False, "isDefault": False},
                ]
            }
        }

        project_route = respx.get(f"{base_url}/projects/123/types").mock(
            return_value=httpx.Response(200, json=project_types_response)
        )

        global_route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(200, json=global_types_response)
        )

        result = await server.call_tool(
            "resolve_type", {"params": {"project_id": 123, "name": "Epic"}}
        )

        assert project_route.called
        assert global_route.called
        response_data = json.loads(result[0].text)
        assert response_data["available_in_project"] is False
        assert "not available in project" in response_data["note"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_type_disambiguation(self, server, base_url):
        """Test disambiguation when multiple types match."""
        import json

        types_response = {
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "name": "Feature",
                        "isMilestone": False,
                        "isDefault": False,
                    },
                    {
                        "id": 2,
                        "name": "Feature",
                        "isMilestone": False,
                        "isDefault": False,
                    },  # Duplicate name
                ]
            }
        }

        route = respx.get(f"{base_url}/projects/123/types").mock(
            return_value=httpx.Response(200, json=types_response)
        )

        result = await server.call_tool(
            "resolve_type", {"params": {"project_id": 123, "name": "Feature"}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["disambiguation_needed"] is True
        assert len(response_data["matches"]) == 2


# ============================================================================
# Test: append_work_package_description
# ============================================================================


class TestAppendWorkPackageDescription:
    """Test suite for append_work_package_description tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_append_description_success(self, server, base_url):
        """Test successful description append."""
        import json

        current_wp = {
            "id": 123,
            "description": {"raw": "Original description"},
            "lockVersion": 5,
        }

        updated_wp = {
            "id": 123,
            "description": {"raw": "Original description\n\nNew content"},
            "lockVersion": 6,
        }

        get_route = respx.get(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(200, json=current_wp)
        )

        patch_route = respx.patch(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(200, json=updated_wp)
        )

        result = await server.call_tool(
            "append_work_package_description",
            {"params": {"wp_id": 123, "markdown": "New content"}},
        )

        assert get_route.called
        assert patch_route.called
        response_data = json.loads(result[0].text)
        assert "Original description" in response_data["description"]["raw"]
        assert "New content" in response_data["description"]["raw"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_append_description_empty_existing(self, server, base_url):
        """Test appending to work package with no existing description."""
        import json

        current_wp = {"id": 123, "description": {"raw": ""}, "lockVersion": 1}

        updated_wp = {
            "id": 123,
            "description": {"raw": "New content"},
            "lockVersion": 2,
        }

        get_route = respx.get(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(200, json=current_wp)
        )

        patch_route = respx.patch(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(200, json=updated_wp)
        )

        result = await server.call_tool(
            "append_work_package_description",
            {"params": {"wp_id": 123, "markdown": "New content"}},
        )

        assert get_route.called
        assert patch_route.called
        response_data = json.loads(result[0].text)
        assert response_data["description"]["raw"] == "New content"

    @respx.mock
    @pytest.mark.asyncio
    async def test_append_description_work_package_not_found(self, server, base_url):
        """Test error when work package doesn't exist."""
        route = respx.get(f"{base_url}/work_packages/99999").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "append_work_package_description",
                {"params": {"wp_id": 99999, "markdown": "Test"}},
            )

        assert route.called
        assert "Resource not found" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_append_description_conflict(self, server, base_url):
        """Test handling of edit conflict (stale lockVersion)."""
        current_wp = {
            "id": 123,
            "description": {"raw": "Original"},
            "lockVersion": 5,
        }

        get_route = respx.get(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(200, json=current_wp)
        )

        patch_route = respx.patch(f"{base_url}/work_packages/123").mock(
            return_value=httpx.Response(
                409, json={"message": "Resource was updated since you started editing"}
            )
        )

        with pytest.raises(ToolError):
            await server.call_tool(
                "append_work_package_description",
                {"params": {"wp_id": 123, "markdown": "New"}},
            )

        assert get_route.called
        assert patch_route.called


# ============================================================================
# Test: list_work_packages
# ============================================================================


class TestListWorkPackages:
    """Test suite for list_work_packages tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_basic(self, server, base_url):
        """Test basic work package listing for a project."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 3,
            "total": 3,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "subject": "Task 1",
                        "_links": {
                            "self": {"href": "/api/v3/work_packages/1"},
                            "project": {"href": "/api/v3/projects/123"},
                        },
                    },
                    {
                        "id": 2,
                        "subject": "Task 2",
                        "_links": {
                            "self": {"href": "/api/v3/work_packages/2"},
                            "project": {"href": "/api/v3/projects/123"},
                        },
                    },
                    {
                        "id": 3,
                        "subject": "Task 3",
                        "_links": {
                            "self": {"href": "/api/v3/work_packages/3"},
                            "project": {"href": "/api/v3/projects/123"},
                        },
                    },
                ]
            },
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages", {"params": {"project_id": 123}}
        )

        assert route.called
        # Verify project filter is applied
        filters_param = route.calls.last.request.url.params.get("filters")
        assert filters_param is not None
        filters = json.loads(filters_param)
        assert filters[0]["project"]["operator"] == "="
        assert filters[0]["project"]["values"] == ["123"]

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 3
        assert len(response_data["_embedded"]["elements"]) == 3

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_with_pagination(self, server, base_url):
        """Test work package listing with pagination."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 2,
            "total": 10,
            "pageSize": 2,
            "offset": 2,
            "_embedded": {
                "elements": [
                    {"id": 3, "subject": "WP 3"},
                    {"id": 4, "subject": "WP 4"},
                ]
            },
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages",
            {"params": {"project_id": 123, "page_size": 2, "offset": 2}},
        )

        assert route.called
        assert route.calls.last.request.url.params.get("pageSize") == "2"
        assert route.calls.last.request.url.params.get("offset") == "2"

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_with_sorting(self, server, base_url):
        """Test work package listing with sorting."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 2,
            "total": 2,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages",
            {"params": {"project_id": 123, "sort_by": "subject"}},
        )

        assert route.called
        sortby_param = route.calls.last.request.url.params.get("sortBy")
        assert sortby_param is not None
        sortby = json.loads(sortby_param)
        assert sortby == [["subject", "asc"]]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_with_desc_sorting(self, server, base_url):
        """Test work package listing with descending sort order."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages",
            {"params": {"project_id": 123, "sort_by": "-updatedAt"}},
        )

        assert route.called
        sortby_param = route.calls.last.request.url.params.get("sortBy")
        sortby = json.loads(sortby_param)
        assert sortby == [["updatedAt", "desc"]]

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_with_filters(self, server, base_url):
        """Test work package listing with additional filters."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 1,
            "total": 1,
            "_embedded": {
                "elements": [
                    {"id": 1, "subject": "Open Task", "status": {"name": "Open"}}
                ]
            },
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages",
            {
                "params": {
                    "project_id": 123,
                    "filters": {"status": {"operator": "o", "values": []}},
                }
            },
        )

        assert route.called
        filters_param = route.calls.last.request.url.params.get("filters")
        filters = json.loads(filters_param)
        # Should have project filter + status filter
        assert len(filters) == 2
        assert filters[0]["project"]["operator"] == "="
        assert filters[1]["status"]["operator"] == "o"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_empty(self, server, base_url):
        """Test listing when no work packages exist."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_work_packages", {"params": {"project_id": 123}}
        )

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_project_not_found(self, server, base_url):
        """Test error when project doesn't exist."""
        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(404, json={"message": "Project not found"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "list_work_packages", {"params": {"project_id": 99999}}
            )

        assert route.called
        assert "Resource not found" in str(exc_info.value)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_work_packages_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        route = respx.get(f"{base_url}/work_packages").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "list_work_packages", {"params": {"project_id": 123}}
            )

        assert route.called
        assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_work_packages_invalid_project_id(self, server):
        """Test validation error for invalid project ID."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "list_work_packages", {"params": {"project_id": 0}}
            )

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_work_packages_invalid_page_size(self, server):
        """Test validation error for invalid page size."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool(
                "list_work_packages", {"params": {"project_id": 123, "page_size": 0}}
            )

        assert "validation" in str(exc_info.value).lower()


# ============================================================================
# Test: list_types
# ============================================================================


class TestListTypes:
    """Test suite for list_types tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_types_basic(self, server, base_url):
        """Test basic type listing."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 4,
            "total": 4,
            "_embedded": {
                "elements": [
                    {
                        "id": 1,
                        "name": "Task",
                        "isMilestone": False,
                        "isDefault": True,
                        "color": "#1A67A3",
                    },
                    {
                        "id": 2,
                        "name": "Bug",
                        "isMilestone": False,
                        "isDefault": False,
                        "color": "#E73E3E",
                    },
                    {
                        "id": 3,
                        "name": "Feature",
                        "isMilestone": False,
                        "isDefault": False,
                        "color": "#32B1A5",
                    },
                    {
                        "id": 4,
                        "name": "Milestone",
                        "isMilestone": True,
                        "isDefault": False,
                        "color": "#D4D4D4",
                    },
                ]
            },
        }

        route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool("list_types", {"params": {}})

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 4
        assert len(response_data["_embedded"]["elements"]) == 4
        # Verify it includes different type attributes
        elements = response_data["_embedded"]["elements"]
        assert any(e["isMilestone"] for e in elements)
        assert any(e["isDefault"] for e in elements)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_types_with_pagination(self, server, base_url):
        """Test type listing with pagination."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 2,
            "total": 5,
            "pageSize": 2,
            "offset": 2,
            "_embedded": {
                "elements": [
                    {"id": 3, "name": "Feature", "isMilestone": False},
                    {"id": 4, "name": "Epic", "isMilestone": False},
                ]
            },
        }

        route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool(
            "list_types", {"params": {"page_size": 2, "offset": 2}}
        )

        assert route.called
        assert route.calls.last.request.url.params.get("pageSize") == "2"
        assert route.calls.last.request.url.params.get("offset") == "2"

        response_data = json.loads(result[0].text)
        assert response_data["count"] == 2
        assert response_data["offset"] == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_types_empty(self, server, base_url):
        """Test listing when no types exist (edge case)."""
        import json

        expected_response = {
            "_type": "Collection",
            "count": 0,
            "total": 0,
            "_embedded": {"elements": []},
        }

        route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(200, json=expected_response)
        )

        result = await server.call_tool("list_types", {"params": {}})

        assert route.called
        response_data = json.loads(result[0].text)
        assert response_data["count"] == 0

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_types_unauthorized(self, server, base_url):
        """Test error handling for unauthorized access."""
        route = respx.get(f"{base_url}/types").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        with pytest.raises(ToolError) as exc_info:
            await server.call_tool("list_types", {"params": {}})

        assert route.called
        assert "Authentication failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_types_invalid_page_size(self, server):
        """Test validation error for invalid page size."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool("list_types", {"params": {"page_size": 0}})

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_types_page_size_too_large(self, server):
        """Test validation error for page size exceeding maximum."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool("list_types", {"params": {"page_size": 2000}})

        assert "validation" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_types_invalid_offset(self, server):
        """Test validation error for invalid offset."""
        with pytest.raises(ToolError) as exc_info:
            await server.call_tool("list_types", {"params": {"offset": 0}})

        assert "validation" in str(exc_info.value).lower()

