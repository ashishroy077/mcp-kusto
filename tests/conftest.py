"""
Test configuration and fixtures for the Kusto MCP tests.
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Add the parent directory to the Python path so we can import src.kusto_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class MockContext:
    """Mock MCP Context for testing"""
    def __init__(self, mock_kusto_manager=None):
        self.lifespan_context = MagicMock()
        if mock_kusto_manager:
            self.lifespan_context.kusto_manager = mock_kusto_manager


class MockResult:
    """Mock Kusto query result"""
    def __init__(self, data=None):
        if data:
            self.primary_results = [data]
        else:
            self.primary_results = []


class TextContent:
    """Mock text content for prompts"""
    def __init__(self, text):
        self.content = text
    
    def __str__(self):
        return self.content


# Create a mock for base Message classes
class UserMessage:
    def __init__(self, content):
        self.content = content
    
    def __str__(self):
        return str(self.content)


class AssistantMessage:
    def __init__(self, content):
        self.content = content
    
    def __str__(self):
        return str(self.content)


# Create a mock VSCode module
class VSCodeWindow:
    @staticmethod
    async def show_input_box(options):
        return "mock_input"

class MockVSCode:
    window = VSCodeWindow()

# Make vscode available for tests
sys.modules["vscode"] = MockVSCode()

# Mock MCP base module
class MockPromptBase:
    Message = TextContent
    UserMessage = UserMessage
    AssistantMessage = AssistantMessage

# Set up mock MCP modules
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.server"] = MagicMock()
sys.modules["mcp.server.fastmcp"] = MagicMock()
sys.modules["mcp.server.fastmcp.prompts"] = MagicMock()
sys.modules["mcp.server.fastmcp.prompts.base"] = MockPromptBase


@pytest.fixture
def mock_kusto_manager():
    """Create a mock KustoConnectionManager"""
    manager = MagicMock()
    manager.current_cluster = "https://mockcluster.kusto.windows.net"
    manager.current_database = "mockdb"
    manager.get_current_connection = AsyncMock(return_value=MagicMock())
    manager.execute_query = AsyncMock(return_value=(True, MockResult()))
    manager.get_tables = AsyncMock(return_value=["table1", "table2"])
    manager.get_table_schema = AsyncMock(return_value={"OrderedColumns": [{"Name": "col1", "Type": "string", "Description": ""}]})
    manager.prompt_for_connection_details = AsyncMock(return_value=(True, "Successfully connected"))
    manager.close_connections = AsyncMock()
    return manager


@pytest.fixture
def mock_context(mock_kusto_manager):
    """Create a mock MCP Context with a mock KustoConnectionManager"""
    return MockContext(mock_kusto_manager)


# Patch out external dependencies to avoid actual network calls
@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    """Patch external dependencies for all tests"""
    # Patch DefaultAzureCredential
    monkeypatch.setattr("azure.identity.DefaultAzureCredential", MagicMock)
    
    # Create a mock vscode module with the functionality we need
    mock_window = MagicMock()
    mock_window.show_input_box = AsyncMock(return_value="mock_input")
    mock_vscode = MagicMock()
    mock_vscode.window = mock_window
    monkeypatch.setattr("src.kusto_mcp.kusto_connection.vscode", mock_vscode)
    
    # Import Path for KustoConnectionManager
    from pathlib import Path
    monkeypatch.setattr("src.kusto_mcp.kusto_connection.Path", Path)
    
    # Additional module mocks can be added here if needed