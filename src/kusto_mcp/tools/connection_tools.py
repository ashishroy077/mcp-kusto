"""
Kusto connection tools - Tools for connecting to Azure Data Explorer (Kusto)
"""

import importlib
from mcp.server.fastmcp import FastMCP, Context

def register_tools(mcp: FastMCP) -> None:
    """Register connection-related tools"""
    
    @mcp.tool()
    async def connect(ctx: Context) -> str:
        """
        Connect to an Azure Kusto cluster and database.
        
        This tool will prompt for connection details using VS Code input boxes and
        establish a connection to the specified Kusto cluster and database.
        """
        # Import dynamically to avoid circular imports
        module = importlib.import_module("kusto_mcp.kusto_connection")
        KustoConnectionManager = getattr(module, "KustoConnectionManager")
        
        # Create a new connection manager
        kusto_manager = KustoConnectionManager()
        
        # Connect to Kusto
        success, message = await kusto_manager.connect()
        
        if not success:
            return f"❌ Failed to connect: {message}"
            
        # Store the connection manager in the context if possible
        if hasattr(ctx, "set_state"):
            try:
                await ctx.set_state("kusto_manager", kusto_manager)
            except Exception as e:
                # If we can't store it, log but continue
                print(f"Warning: Couldn't store connection manager in context: {e}")
        
        return f"✅ {message}"
    
    @mcp.tool()
    async def connection_status(ctx: Context) -> str:
        """
        Check the current Kusto connection status.
        
        Returns information about the currently connected cluster and database.
        """
        # Get the connection manager - try from context state first, then create new instance
        kusto_manager = None
        
        try:
            if hasattr(ctx, "get_state"):
                try:
                    kusto_manager = await ctx.get_state("kusto_manager")
                except:
                    # State might not be available or set
                    pass
            
            if not kusto_manager:
                # Import dynamically to avoid circular imports
                module = importlib.import_module("kusto_mcp.kusto_connection")
                KustoConnectionManager = getattr(module, "KustoConnectionManager")
                kusto_manager = KustoConnectionManager()
        except Exception as e:
            return f"❌ Error initializing Kusto connection: {str(e)}"
            
        # Check if connected
        if not kusto_manager.is_connected():
            return "❌ Not connected to any Kusto cluster.\n\nUse the `connect` tool to establish a connection."
            
        # Get connection details
        cluster, database = kusto_manager.get_connection_details()
        
        return f"""✅ Currently connected to:
        
- **Cluster**: {cluster}
- **Database**: {database}
"""