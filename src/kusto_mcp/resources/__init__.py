"""
Kusto MCP Resources - Resources for exposing Kusto data schemas
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context

def register_resources(mcp: FastMCP) -> None:
    """Register all Kusto-related resources with the MCP server"""
    from . import schemas
    schemas.register_resources(mcp)