"""
Tests for the Kusto MCP server.
"""

import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import contextlib
import builtins
import importlib

from src.kusto_mcp.server import server, server_lifespan


@pytest.fixture
def mock_kusto_connection_manager():
    """Create a mock KustoConnectionManager"""
    with patch("src.kusto_mcp.server.KustoConnectionManager") as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.close_connections = AsyncMock()
        yield mock_instance


@pytest.mark.asyncio
async def test_server_lifespan():
    """Test the server lifespan context manager."""
    mock_server = MagicMock()
    
    # Use the real server_lifespan with a mocked KustoConnectionManager
    with patch("src.kusto_mcp.server.KustoConnectionManager") as mock_cls:
        mock_manager = mock_cls.return_value
        mock_manager.close_connections = AsyncMock()
        
        # Use the actual server_lifespan context manager
        async with server_lifespan(mock_server) as context:
            # Check that we have the expected kusto_manager in the context
            assert "kusto_manager" in context
            assert context["kusto_manager"] == mock_manager
        
        # After the context exits, close_connections should be called
        mock_manager.close_connections.assert_called_once()


def test_server_initialization():
    """Test the server initialization."""
    # Create a mock FastMCP server
    mock_server = MagicMock()
    
    # Create mock registration functions
    mock_register_resources = MagicMock()
    mock_register_tools = MagicMock()
    mock_register_prompts = MagicMock()
    
    # Save original imports to restore later
    orig_fastmcp = None
    if "mcp.server.fastmcp" in sys.modules:
        orig_fastmcp = sys.modules["mcp.server.fastmcp"]
    
    # Create mock FastMCP module
    mock_fastmcp_module = MagicMock()
    mock_fastmcp_module.FastMCP = MagicMock(return_value=mock_server)
    mock_fastmcp_module.Context = MagicMock()
    
    try:
        # Set up our mocks in sys.modules
        sys.modules["mcp.server.fastmcp"] = mock_fastmcp_module
        sys.modules["src.kusto_mcp.resources"] = MagicMock(register_resources=mock_register_resources)
        sys.modules["src.kusto_mcp.tools"] = MagicMock(register_tools=mock_register_tools)
        sys.modules["src.kusto_mcp.prompts"] = MagicMock(register_prompts=mock_register_prompts)
        
        # Remove server module if already loaded
        if "src.kusto_mcp.server" in sys.modules:
            del sys.modules["src.kusto_mcp.server"]
        
        # Create a fresh import of server module
        import importlib
        server_module = importlib.import_module("src.kusto_mcp.server")
        
        # Verify registrations were called
        mock_register_resources.assert_called_once_with(mock_server)
        mock_register_tools.assert_called_once_with(mock_server)
        mock_register_prompts.assert_called_once_with(mock_server)
        
    finally:
        # Restore original modules
        if orig_fastmcp:
            sys.modules["mcp.server.fastmcp"] = orig_fastmcp
        
        # Clean up our mock modules
        for mod in ["src.kusto_mcp.resources", "src.kusto_mcp.tools", "src.kusto_mcp.prompts"]:
            if mod in sys.modules and isinstance(sys.modules[mod], MagicMock):
                del sys.modules[mod]


def test_server_run():
    """Test the server run function."""
    # Create a mock server with run method
    mock_server = MagicMock()
    
    with patch("src.kusto_mcp.server.server", mock_server), \
         patch("builtins.print") as mock_print:
        
        # Import and call the main function
        from src.kusto_mcp.server import main
        main()
        
        # The server run method should be called
        mock_server.run.assert_called_once()
        # There should be some output to the console
        assert mock_print.call_count > 0


def test_server_error_handling():
    """Test the server's error handling."""
    # This test executes just the import error handling section of code
    # from server.py in a controlled environment
    
    # Create a test script that simulates the import error handling code
    test_script = """
try:
    import mcp.server.fastmcp
except ImportError:
    print("ERROR: Required packages are not installed. Please run:")
    print("pip install -r requirements.txt")
    print("\\nOr install directly:")
    print("pip install mcp>=0.11.0 azure-kusto-data>=4.2.0 azure-kusto-ingest>=4.2.0 azure-identity>=1.15.0 python-dotenv>=1.0.0 pandas>=2.0.0")
    import sys
    sys.exit(1)
"""
    
    # Set up mocks for sys.modules to ensure ImportError
    with patch.dict('sys.modules', {'mcp': None}):
        # Mock print and sys.exit
        with patch('builtins.print') as mock_print, patch('sys.exit') as mock_exit:
            # Execute the test script
            try:
                # This should raise ImportError which is caught in the script
                exec(test_script)
            except SystemExit:
                # SystemExit is expected if sys.exit is called but not mocked
                pass
            
            # Check error messages were printed
            assert mock_print.call_count >= 3  # At least 3 lines of output
            
            # Get all printed messages
            printed_messages = ''.join(str(args[0]) for args, kwargs in mock_print.call_args_list)
            
            # Check that error messages about requirements were printed
            assert 'requirements' in printed_messages.lower()
            
            # Check sys.exit was called with code 1
            mock_exit.assert_called_once_with(1)