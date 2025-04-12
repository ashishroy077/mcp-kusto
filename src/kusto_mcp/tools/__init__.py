"""
Kusto MCP Tools - Tools for working with Kusto data
"""

from mcp.server.fastmcp import FastMCP

def register_tools(mcp: FastMCP) -> None:
    """Register all Kusto-related tools with the MCP server"""
    from . import query_tools, connection_tools
    
    query_tools.register_tools(mcp)
    connection_tools.register_tools(mcp)