#!/usr/bin/env python3
"""
Azure Kusto MCP Server

This MCP server connects to Azure Kusto and provides:
- Resources for table schemas
- Tools for running KQL queries
- Prompts for common data analysis tasks

This server follows Azure best practices for authentication and data handling.
"""

import os
import sys
import importlib.util

# Add parent directory to path for direct script execution
if __name__ == "__main__" and not __package__:
    # Add the parent directory to sys.path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    # Set the package name
    __package__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

# Check for required dependencies before importing them
try:
    import mcp.server.fastmcp
except ImportError:
    print("ERROR: Required packages are not installed. Please run:")
    print("pip install -r requirements.txt")
    print("\nOr install directly:")
    print("pip install mcp>=0.11.0 azure-kusto-data>=4.2.0 azure-kusto-ingest>=4.2.0 azure-identity>=1.15.0 python-dotenv>=1.0.0 pandas>=2.0.0")
    sys.exit(1)

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

# Local imports - handle both direct execution and module import
try:
    from .kusto_connection import KustoConnectionManager
    from .resources import register_resources
    from .tools import register_tools
    from .prompts import register_prompts
except ImportError:
    # Fallback for direct script execution
    from kusto_mcp.kusto_connection import KustoConnectionManager
    from kusto_mcp.resources import register_resources
    from kusto_mcp.tools import register_tools
    from kusto_mcp.prompts import register_prompts

# Load environment variables from .env file if present
load_dotenv()

# Create the MCP server instance
server = FastMCP(
    "Azure Kusto MCP Server",
    description="Connect to Azure Kusto, explore schemas, and run KQL queries",
    dependencies=["azure-kusto-data", "azure-kusto-ingest", "azure-identity", "pandas"]
)

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """
    Manage Kusto connection in server lifecycle
    
    This context manager initializes the Kusto connection manager
    when the server starts and cleans up connections when it stops.
    """
    # Initialize Kusto connection manager
    connection_manager = KustoConnectionManager()
    
    try:
        # Create the context dictionary
        context_dict = {"kusto_manager": connection_manager}
        
        # Try to make the connection manager available in all possible ways
        # to ensure maximum compatibility with different MCP versions
        
        # Directly attach to server if possible
        if hasattr(server, "kusto_manager"):
            server.kusto_manager = connection_manager
        
        # Add to server state if it exists
        if hasattr(server, "state") and isinstance(server.state, dict):
            server.state["kusto_manager"] = connection_manager
            
        # Make it available to the Context objects
        yield context_dict
    finally:
        # Cleanup connections when server shuts down
        await connection_manager.close_connections()

# Register lifespan handler
server.lifespan = server_lifespan

# Register all resources, tools, and prompts
register_resources(server)
register_tools(server)
register_prompts(server)

def main():
    """
    Main entry point for the Kusto MCP server.
    
    This function is used by the command-line script when installed via pip.
    """
    print("Starting Azure Kusto MCP Server...")
    print("To connect to a Kusto cluster, use the 'connect' tool.")
    server.run()

if __name__ == "__main__":
    # Run the server
    main()