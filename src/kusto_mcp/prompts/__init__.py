"""
Kusto MCP Prompts - Prompts for common Kusto data analysis tasks
"""

from mcp.server.fastmcp import FastMCP

def register_prompts(mcp: FastMCP) -> None:
    """Register all Kusto-related prompts with the MCP server"""
    from . import analysis_prompts
    
    analysis_prompts.register_prompts(mcp)