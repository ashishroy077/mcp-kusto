"""
Kusto schema resources - Expose Kusto table schemas as MCP resources
"""

import json
from typing import Dict, Any, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP, Context
from ..kusto_connection import KustoConnectionManager


# Store a singleton instance for testing injection
_connection_manager = None

def get_connection_manager():
    """Get the current KustoConnectionManager instance or create a new one"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = KustoConnectionManager()
    return _connection_manager

def set_connection_manager(manager):
    """Set the KustoConnectionManager instance (for testing)"""
    global _connection_manager
    _connection_manager = manager

def register_resources(mcp: FastMCP) -> None:
    """Register schema-related resources"""
    
    # Updated to use proper URL formatting for resources
    
    @mcp.resource("https://kusto-mcp.example/kusto/tables")
    async def list_tables():
        """List all available tables in the current Kusto database"""
        connection_manager = get_connection_manager()
        
        tables = await connection_manager.get_tables()
        
        if not tables:
            return "No tables available. Please ensure you're connected to a Kusto database."
            
        result = "# Available Kusto Tables\n\n"
        for table in sorted(tables):
            result += f"- {table}\n"
        
        result += "\nTo view a table schema, access the resource: `kusto/schema/{table_name}`"
        return result
    
    @mcp.resource("https://kusto-mcp.example/kusto/schema/{table_name}")
    async def get_table_schema(table_name):
        """Get the schema for a specific Kusto table"""
        connection_manager = get_connection_manager()
        
        schema = await connection_manager.get_table_schema(table_name)
        
        if not schema:
            return f"Schema for table '{table_name}' not found or not accessible."
            
        result = f"# Schema for Kusto Table: {table_name}\n\n"
        result += "## Columns\n\n"
        result += "| Name | Type | Description |\n"
        result += "| ---- | ---- | ----------- |\n"
        
        # Format columns
        for column in schema.get("OrderedColumns", []):
            col_name = column.get("Name", "")
            col_type = column.get("Type", "")
            col_desc = column.get("Description", "").replace("\n", " ") or "-"
            result += f"| {col_name} | {col_type} | {col_desc} |\n"
            
        return result
    
    @mcp.resource("https://kusto-mcp.example/kusto/sample")
    async def get_kusto_sample():
        """Provide a sample KQL query and its explanation"""
        sample = {
            "query": "StormEvents | where StartTime >= datetime(2007-11-01) and StartTime < datetime(2007-12-01) | where State == 'FLORIDA' | count",
            "explanation": "This query filters the StormEvents table to find events in Florida during November 2007, then counts the total number of matching events.",
            "queryParts": [
                {"part": "StormEvents", "explanation": "The source table containing storm data"},
                {"part": "where StartTime >= datetime(2007-11-01) and StartTime < datetime(2007-12-01)", "explanation": "Filters events to a specific date range"},
                {"part": "where State == 'FLORIDA'", "explanation": "Further filters to only include events in Florida"},
                {"part": "count", "explanation": "Counts the total number of matching records"}
            ],
            "commonOperators": [
                {"operator": "where", "description": "Filters a table to the subset of rows that satisfy a predicate"},
                {"operator": "summarize", "description": "Produces a table that aggregates the content of the input table"},
                {"operator": "join", "description": "Merges the rows of two tables to form a new table"},
                {"operator": "project", "description": "Selects a subset of columns to include in results"}
            ]
        }
        
        return json.dumps(sample, indent=2)
    
    @mcp.resource("https://kusto-mcp.example/kusto/connection")
    async def get_connection_info():
        """Provide information about the current Kusto connection"""
        connection_manager = get_connection_manager()
        
        cluster = connection_manager.current_cluster
        database = connection_manager.current_database
        
        if not cluster or not database:
            return "Not connected to any Kusto cluster. Use the `connect` tool to establish a connection."
            
        return f"""# Kusto Connection Information

- **Cluster:** {cluster}
- **Database:** {database}

To change the connection, use the `connect` tool.
"""