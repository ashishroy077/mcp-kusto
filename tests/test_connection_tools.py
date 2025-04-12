"""
Tests for the Kusto connection tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.kusto_mcp.tools.connection_tools import register_tools


class MockFastMCP:
    """Mock FastMCP for testing tool registration."""
    
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


@pytest.fixture
def mock_mcp():
    """Create a mock MCP instance."""
    return MockFastMCP()


@pytest.fixture
def register_connection_tools(mock_mcp):
    """Register connection tools with mock MCP."""
    register_tools(mock_mcp)
    return mock_mcp


@pytest.mark.asyncio
async def test_connect_success(register_connection_tools, mock_context):
    """Test connect tool with successful connection."""
    mock_context.lifespan_context.kusto_manager.prompt_for_connection_details.return_value = (
        True, "Successfully connected to testdb at https://testcluster.kusto.windows.net"
    )
    
    result = await register_connection_tools.tools["connect"](mock_context)
    
    assert "✅" in result
    assert "Successfully connected" in result
    mock_context.lifespan_context.kusto_manager.prompt_for_connection_details.assert_called_once()


@pytest.mark.asyncio
async def test_connect_failure(register_connection_tools, mock_context):
    """Test connect tool with failed connection."""
    mock_context.lifespan_context.kusto_manager.prompt_for_connection_details.return_value = (
        False, "Failed to connect"
    )
    
    result = await register_connection_tools.tools["connect"](mock_context)
    
    assert "❌" in result
    assert "Failed to connect" in result
    mock_context.lifespan_context.kusto_manager.prompt_for_connection_details.assert_called_once()


@pytest.mark.asyncio
async def test_connection_status_connected(register_connection_tools, mock_context):
    """Test connection_status tool when connected."""
    mock_context.lifespan_context.kusto_manager.current_cluster = "https://testcluster.kusto.windows.net"
    mock_context.lifespan_context.kusto_manager.current_database = "testdb"
    mock_context.lifespan_context.kusto_manager.get_current_connection = AsyncMock(return_value=MagicMock())
    
    result = await register_connection_tools.tools["connection_status"](mock_context)
    
    assert "✅" in result
    assert "Connected to Azure Kusto" in result
    assert "testcluster" in result
    assert "testdb" in result
    mock_context.lifespan_context.kusto_manager.get_current_connection.assert_called_once()


@pytest.mark.asyncio
async def test_connection_status_not_connected(register_connection_tools, mock_context):
    """Test connection_status tool when not connected."""
    mock_context.lifespan_context.kusto_manager.current_cluster = None
    mock_context.lifespan_context.kusto_manager.current_database = None
    
    result = await register_connection_tools.tools["connection_status"](mock_context)
    
    assert "⚠️" in result
    assert "Not connected" in result
    assert "connect" in result


@pytest.mark.asyncio
async def test_connection_status_invalid(register_connection_tools, mock_context):
    """Test connection_status tool when connection is invalid."""
    mock_context.lifespan_context.kusto_manager.current_cluster = "https://testcluster.kusto.windows.net"
    mock_context.lifespan_context.kusto_manager.current_database = "testdb"
    mock_context.lifespan_context.kusto_manager.get_current_connection = AsyncMock(return_value=None)
    
    result = await register_connection_tools.tools["connection_status"](mock_context)
    
    assert "⚠️" in result
    assert "Connection" in result
    assert "invalid" in result or "inactive" in result
    assert "reconnect" in result