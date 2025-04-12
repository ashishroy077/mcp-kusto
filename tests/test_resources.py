"""
Tests for the Kusto resources.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.kusto_mcp.resources.schemas import register_resources, set_connection_manager


class MockFastMCP:
    """Mock FastMCP for testing resource registration."""
    
    def __init__(self):
        self.resources = {}
    
    def resource(self, url):
        def decorator(func):
            self.resources[url] = func
            return func
        return decorator


@pytest.fixture
def mock_kusto_manager():
    """Create a mock KustoConnectionManager"""
    mock_manager = MagicMock()
    mock_manager.get_tables = AsyncMock(return_value=["table1", "table2", "table3"])
    mock_manager.get_table_schema = AsyncMock(return_value={
        "OrderedColumns": [
            {"Name": "col1", "Type": "string", "Description": "First column"},
            {"Name": "col2", "Type": "int", "Description": "Second column"},
        ]
    })
    mock_manager.current_cluster = "https://testcluster.kusto.windows.net"
    mock_manager.current_database = "testdb"
    return mock_manager


@pytest.fixture
def mock_mcp():
    """Create a mock MCP instance."""
    return MockFastMCP()


@pytest.fixture
def register_schema_resources(mock_mcp, mock_kusto_manager):
    """Register schema resources with mock MCP."""
    # Inject our mock kusto manager
    set_connection_manager(mock_kusto_manager)
    register_resources(mock_mcp)
    return mock_mcp


@pytest.mark.asyncio
async def test_list_tables_resource(register_schema_resources):
    """Test the kusto/tables resource."""
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/tables"]()
    
    # Verify the results
    assert "Available Kusto Tables" in result
    assert "table1" in result
    assert "table2" in result
    assert "table3" in result
    assert "kusto/schema" in result


@pytest.mark.asyncio
async def test_list_tables_resource_empty(register_schema_resources, mock_kusto_manager):
    """Test the kusto/tables resource with no tables."""
    # Override the mock to return no tables
    mock_kusto_manager.get_tables.return_value = []
    
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/tables"]()
    
    # Verify the results
    assert "No tables available" in result


@pytest.mark.asyncio
async def test_get_table_schema_resource(register_schema_resources):
    """Test the kusto/schema/{table_name} resource."""
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/schema/{table_name}"]("test_table")
    
    # Verify the results
    assert "Schema for Kusto Table: test_table" in result
    assert "col1" in result
    assert "col2" in result
    assert "string" in result
    assert "int" in result
    assert "First column" in result
    assert "Second column" in result


@pytest.mark.asyncio
async def test_get_table_schema_resource_not_found(register_schema_resources, mock_kusto_manager):
    """Test the kusto/schema/{table_name} resource when schema is not found."""
    # Override the mock to return None for the schema
    mock_kusto_manager.get_table_schema.return_value = None
    
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/schema/{table_name}"]("nonexistent_table")
    
    # Verify the results
    assert "not found" in result.lower() or "not accessible" in result.lower()
    assert "nonexistent_table" in result


@pytest.mark.asyncio
async def test_get_kusto_sample_resource(register_schema_resources):
    """Test the kusto/sample resource."""
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/sample"]()
    
    # Verify the result is valid JSON
    sample = json.loads(result)
    assert "query" in sample
    assert "explanation" in sample or "queryParts" in sample
    
    # Check some expected content
    assert "where" in result.lower() or "join" in result.lower() or "project" in result.lower()


@pytest.mark.asyncio
async def test_get_connection_info_resource(register_schema_resources):
    """Test the kusto/connection resource with an active connection."""
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/connection"]()
    
    # Verify the results
    assert "Kusto Connection Information" in result
    assert "testcluster" in result
    assert "testdb" in result


@pytest.mark.asyncio
async def test_get_connection_info_resource_no_connection(register_schema_resources, mock_kusto_manager):
    """Test the kusto/connection resource with no active connection."""
    # Override the mock to return None for cluster and database
    mock_kusto_manager.current_cluster = None
    mock_kusto_manager.current_database = None
    
    # Execute the resource function
    result = await register_schema_resources.resources["https://kusto-mcp.example/kusto/connection"]()
    
    # Verify the results
    assert "Not connected" in result
    assert "connect" in result