"""
Kusto connection tools - Tools for connecting to Azure Data Explorer (Kusto)
"""

import importlib
import json
import sys
from mcp.server.fastmcp import FastMCP, Context

# Define a proper logging function for MCP protocol
def log_message(message, type="info"):
    """Log messages in MCP protocol format"""
    msg = {"type": type, "message": message}
    print(json.dumps(msg), flush=True)

def register_tools(mcp: FastMCP) -> None:
    """Register connection-related tools"""
    
    # Log registration
    try:
        log_message("Registering connection tools")
    except Exception as e:
        print(f"Warning: Could not log registration: {str(e)}")
    
    @mcp.tool()
    async def connect(ctx: Context) -> str:
        """
        Connect to an Azure Kusto cluster and database.
        
        This tool will prompt for connection details using VS Code input boxes and
        establish a connection to the specified Kusto cluster and database.
        """
        # Import dynamically to avoid circular imports
        try:
            # First try a direct import of the module which should work in tests
            # since sys.path is modified in conftest.py
            from src.kusto_mcp.kusto_connection import KustoConnectionManager
        except ImportError:
            try:
                # Try absolute import next (for normal operation)
                module = importlib.import_module("kusto_mcp.kusto_connection")
                KustoConnectionManager = getattr(module, "KustoConnectionManager")
            except ModuleNotFoundError:
                # Fallback to relative import (for testing)
                module = importlib.import_module("..kusto_connection", package="kusto_mcp.tools")
                KustoConnectionManager = getattr(module, "KustoConnectionManager")
        
        # Try to get the connection manager from context if available
        kusto_manager = None
        if hasattr(ctx, "lifespan_context") and hasattr(ctx.lifespan_context, "kusto_manager"):
            kusto_manager = ctx.lifespan_context.kusto_manager
            log_message("Using connection manager from lifespan context")
        else:
            # Create a new connection manager
            kusto_manager = KustoConnectionManager()
            log_message("Created new connection manager instance")
        
        # Connect to Kusto
        log_message("Initiating connection to Kusto...")
        success, message = await kusto_manager.prompt_for_connection_details()
        
        if not success:
            return f"❌ Failed to connect: {message}"
            
        # Store the connection manager in the context if possible
        if hasattr(ctx, "set_state"):
            try:
                await ctx.set_state("kusto_manager", kusto_manager)
                log_message("Stored connection manager in context state")
            except Exception as e:
                # If we can't store it, log but continue
                log_message(f"Warning: Couldn't store connection manager in context: {e}", "warning")
        
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
            if hasattr(ctx, "lifespan_context") and hasattr(ctx.lifespan_context, "kusto_manager"):
                kusto_manager = ctx.lifespan_context.kusto_manager
                log_message("Using connection manager from lifespan context")
            elif hasattr(ctx, "get_state"):
                try:
                    kusto_manager = await ctx.get_state("kusto_manager")
                    log_message("Using connection manager from context state")
                except:
                    # State might not be available or set
                    pass
            
            if not kusto_manager:
                # Import dynamically to avoid circular imports
                try:
                    # First try a direct import of the module which should work in tests
                    from src.kusto_mcp.kusto_connection import KustoConnectionManager
                except ImportError:
                    try:
                        # Try absolute import next (for normal operation)
                        module = importlib.import_module("kusto_mcp.kusto_connection")
                        KustoConnectionManager = getattr(module, "KustoConnectionManager")
                    except ModuleNotFoundError:
                        # Fallback to relative import (for testing)
                        module = importlib.import_module("..kusto_connection", package="kusto_mcp.tools")
                        KustoConnectionManager = getattr(module, "KustoConnectionManager")
                        
                kusto_manager = KustoConnectionManager()
                log_message("Created new connection manager instance")
        except Exception as e:
            return f"❌ Error initializing Kusto connection: {str(e)}"
            
        # Check if we have a valid cluster and database for connection
        if (not kusto_manager.current_cluster or not kusto_manager.current_database or 
            kusto_manager.current_cluster == "Not connected" or 
            kusto_manager.current_database == "Not connected"):
            return """⚠️ Not connected to any Kusto cluster.

Use the `connect` tool to establish a connection."""
            
        # Get connection details - handle case where get_connection_details returns no values
        try:
            cluster, database = kusto_manager.get_connection_details()
        except (ValueError, TypeError):
            # Handle the case where get_connection_details doesn't return expected values
            cluster = kusto_manager.current_cluster or "Not connected"
            database = kusto_manager.current_database or "Not connected"
        
        # Get current connection to check if it's valid
        connection = None
        if hasattr(kusto_manager, "get_current_connection"):
            try:
                connection = await kusto_manager.get_current_connection()
            except Exception:
                pass
        
        if not connection:
            return f"""⚠️ Connection to Azure Kusto appears to be invalid or inactive.
            
- **Cluster**: {cluster}
- **Database**: {database}

Please use the `connect` tool to reconnect."""
        
        return f"""✅ Connected to Azure Kusto.
        
- **Cluster**: {cluster}
- **Database**: {database}
"""