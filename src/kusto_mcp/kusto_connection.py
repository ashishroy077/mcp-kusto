"""
Kusto Connection Manager - Handle connections to Azure Kusto.

This module manages connections to Azure Kusto clusters using best practices
for authentication and configuration.
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
import asyncio
from pathlib import Path

import azure.kusto.data as kd
from azure.kusto.data.exceptions import KustoServiceError, KustoAuthenticationError
from azure.identity import DefaultAzureCredential
from mcp.server.fastmcp import Context

# Try to import vscode module, but provide fallbacks if not available
try:
    import vscode
    VSCODE_AVAILABLE = True
except ImportError:
    VSCODE_AVAILABLE = False
    # Define a simple class to provide fallback behavior
    class VSCodeFallback:
        class window:
            @staticmethod
            async def show_input_box(options):
                prompt = options.get("prompt", "")
                default = options.get("value", "")
                print(f"\n{prompt}")
                print(f"Default: {default}")
                return input("Value: ") or default
    
    vscode = VSCodeFallback()

class KustoConnectionManager:
    """
    Manages connections to Azure Kusto clusters.
    
    Uses DefaultAzureCredential for authentication and provides methods
    for querying and managing Kusto resources.
    """
    
    def __init__(self):
        self.connections: Dict[str, kd.KustoClient] = {}
        self.current_cluster: Optional[str] = None
        self.current_database: Optional[str] = None
        # Check for environment variables first
        if os.environ.get("AZURE_KUSTO_CLUSTER") and os.environ.get("AZURE_KUSTO_DATABASE"):
            self.current_cluster = os.environ.get("AZURE_KUSTO_CLUSTER")
            self.current_database = os.environ.get("AZURE_KUSTO_DATABASE")
            print(f"Using Kusto cluster from environment: {self.current_cluster}")
        else:
            self.config_file = Path.home() / ".kusto_mcp_config.json"
            self._load_config()
    
    def _load_config(self) -> None:
        """Load saved configuration if available"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.current_cluster = config.get("cluster")
                    self.current_database = config.get("database")
            except (json.JSONDecodeError, IOError):
                # If config file is corrupted or can't be read, use defaults
                pass
    
    def _save_config(self) -> None:
        """Save current configuration"""
        config = {
            "cluster": self.current_cluster,
            "database": self.current_database
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
        except IOError:
            # Log error but continue if config can't be saved
            print(f"Warning: Could not save configuration to {self.config_file}")
    
    async def initialize_connection(self, cluster: str, database: str) -> bool:
        """
        Initialize a connection to a Kusto cluster.
        
        Args:
            cluster: The Kusto cluster URL (e.g., "https://mycluster.kusto.windows.net")
            database: The name of the database
        
        Returns:
            True if connection was successful, False otherwise
        """
        # Check if we already have this connection
        connection_key = f"{cluster}:{database}"
        
        if connection_key in self.connections:
            self.current_cluster = cluster
            self.current_database = database
            self._save_config()
            return True
        
        try:
            # Use DefaultAzureCredential for authentication
            credential = DefaultAzureCredential()
            
            # Create Kusto client
            client = kd.KustoClient(
                cluster,
                kd.KustoConnectionStringBuilder.with_aad_application_token_authentication(
                    connection_string=cluster, 
                    aad_app_token=credential.get_token("https://kusto.windows.net/.default").token
                )
            )
            
            # Test connection with a simple query
            await asyncio.to_thread(
                client.execute_query,
                database,
                ".show database schema | limit 1"  # Simple query to test connection
            )
            
            # If we got here, the connection was successful
            self.connections[connection_key] = client
            self.current_cluster = cluster
            self.current_database = database
            self._save_config()
            return True
            
        except KustoAuthenticationError:
            return False
        except KustoServiceError:
            return False
        except Exception:
            return False
    
    async def get_current_connection(self) -> Optional[kd.KustoClient]:
        """
        Get the current Kusto client connection.
        
        Returns:
            KustoClient if a current connection exists, None otherwise
        """
        if not self.current_cluster or not self.current_database:
            return None
            
        connection_key = f"{self.current_cluster}:{self.current_database}"
        return self.connections.get(connection_key)
    
    async def execute_query(self, query: str) -> Tuple[bool, Any]:
        """
        Execute a KQL query against the current connection.
        
        Args:
            query: KQL query string
        
        Returns:
            Tuple of (success, result)
            - If successful: (True, query results)
            - If failure: (False, error message)
        """
        client = await self.get_current_connection()
        if not client:
            return False, "No active connection. Please connect to a Kusto cluster first."
        
        try:
            result = await asyncio.to_thread(
                client.execute_query, 
                self.current_database, 
                query
            )
            return True, result
        except Exception as e:
            return False, str(e)
    
    async def get_tables(self) -> List[str]:
        """Get list of tables in the current database"""
        client = await self.get_current_connection()
        if not client or not self.current_database:
            return []
        
        try:
            success, result = await self.execute_query(".show tables | project TableName")
            if success and hasattr(result, 'primary_results') and result.primary_results:
                return [row["TableName"] for row in result.primary_results[0]]
            return []
        except Exception:
            return []
    
    async def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table schema information or None if not found
        """
        client = await self.get_current_connection()
        if not client or not self.current_database:
            return None
            
        try:
            success, result = await self.execute_query(f".show table {table_name} schema as json")
            if success and hasattr(result, 'primary_results') and result.primary_results:
                # The result is a JSON string we need to parse
                schema_json = result.primary_results[0][0]["Schema"]
                return json.loads(schema_json)
            return None
        except Exception:
            return None
    
    async def prompt_for_connection_details(self) -> Tuple[bool, str]:
        """
        Prompt the user for Kusto connection details.
        Uses VS Code API if available, otherwise falls back to console input.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # If environment variables are set, use those
            env_cluster = os.environ.get("AZURE_KUSTO_CLUSTER")
            env_database = os.environ.get("AZURE_KUSTO_DATABASE")
            
            if env_cluster and env_database:
                # Try to connect using environment variables
                success = await self.initialize_connection(env_cluster, env_database)
                if success:
                    return True, f"Successfully connected to {env_database} at {env_cluster} using environment variables"
                else:
                    return False, "Failed to connect using environment variables. Please check credentials and try again."
            
            # Prompt for cluster URL
            cluster_input = await vscode.window.show_input_box({
                "prompt": "Enter the Kusto cluster URL (e.g., https://mycluster.kusto.windows.net)",
                "value": self.current_cluster or ""
            })
            
            if not cluster_input:
                return False, "Cluster URL is required"
                
            # Prompt for database name
            database_input = await vscode.window.show_input_box({
                "prompt": "Enter the Kusto database name",
                "value": self.current_database or ""
            })
            
            if not database_input:
                return False, "Database name is required"
                
            # Try to initialize the connection
            success = await self.initialize_connection(cluster_input, database_input)
            if success:
                return True, f"Successfully connected to {database_input} at {cluster_input}"
            else:
                return False, "Failed to connect. Please check your credentials and try again."
                
        except Exception as e:
            return False, f"Error configuring connection: {str(e)}"
            
    async def close_connections(self) -> None:
        """Close all connections when shutting down"""
        self.connections.clear()
    
    async def connect(self) -> Tuple[bool, str]:
        """
        Interactive connection to Kusto with VS Code input prompts.
        
        Returns:
            Tuple of (success, message)
        """
        # Get cluster URL
        cluster_default = self.current_cluster or "https://kustocluster.region.kusto.windows.net"
        cluster = await vscode.window.show_input_box({
            "prompt": "Enter Kusto cluster URL",
            "value": cluster_default
        })
        
        if not cluster:
            return False, "Connection cancelled - no cluster specified"
            
        # Get database name
        db_default = self.current_database or "database"
        database = await vscode.window.show_input_box({
            "prompt": "Enter database name",
            "value": db_default
        })
        
        if not database:
            return False, "Connection cancelled - no database specified"
            
        # Initialize the connection
        success = await self.initialize_connection(cluster, database)
        
        if success:
            return True, f"Connected to {cluster}, database: {database}"
        else:
            return False, "Failed to connect. Please check your credentials and connection details."
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to a Kusto cluster.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.current_cluster or not self.current_database:
            return False
            
        connection_key = f"{self.current_cluster}:{self.current_database}"
        return connection_key in self.connections
    
    def get_connection_details(self) -> Tuple[str, str]:
        """
        Get the details of the current connection.
        
        Returns:
            Tuple of (cluster, database)
        """
        return self.current_cluster or "Not connected", self.current_database or "Not connected"