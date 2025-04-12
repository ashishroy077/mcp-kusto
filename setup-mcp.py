#!/usr/bin/env python3
"""
Setup script for Azure Kusto MCP Server

This script installs all required dependencies for the MCP server.
"""

import subprocess
import sys
import os

def main():
    print("Setting up Azure Kusto MCP Server...")
    
    # Get the absolute path to the workspace directory
    workspace_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("Error: pip is not available. Please install pip first.")
        sys.exit(1)
    
    # Install required packages
    print("Installing required packages...")
    packages = [
        "mcp>=0.11.0",
        "azure-kusto-data>=4.2.0",
        "azure-kusto-ingest>=4.2.0",
        "azure-identity>=1.15.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.0.0"
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("✅ All dependencies installed successfully!")
        
        # Create .vscode directory if it doesn't exist
        os.makedirs(".vscode", exist_ok=True)
        
        # Create a properly formatted mcp.json configuration file with absolute paths
        mcp_config = """{
  "inputs": [
    {
      "type": "promptString",
      "id": "kusto-cluster",
      "description": "Azure Kusto Cluster URL (e.g., https://mycluster.kusto.windows.net)",
      "default": ""
    },
    {
      "type": "promptString",
      "id": "kusto-database",
      "description": "Azure Kusto Database Name",
      "default": ""
    }
  ],
  "servers": {
    "Azure Kusto MCP": {
      "type": "stdio",
      "command": "%s",
      "args": ["%s/src/kusto_mcp/server.py"],
      "env": {
        "AZURE_KUSTO_CLUSTER": "${input:kusto-cluster}",
        "AZURE_KUSTO_DATABASE": "${input:kusto-database}",
        "PYTHONPATH": "%s"
      }
    }
  }
}""" % (sys.executable.replace('\\', '\\\\'), workspace_dir.replace('\\', '\\\\'), workspace_dir.replace('\\', '\\\\'))
        
        with open(os.path.join(".vscode", "mcp.json"), "w") as f:
            f.write(mcp_config)
            
        print("✅ MCP configuration created in .vscode/mcp.json")
        print("\nSetup complete! You can now use the MCP server in VS Code:")
        print("1. Install the GitHub Copilot extension")
        print("2. Run 'MCP: Start Server with Configuration' from the VS Code command palette")
        print("3. Select 'Azure Kusto MCP' server")
        
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies. Please try manually with:")
        print("pip install mcp>=0.11.0 azure-kusto-data>=4.2.0 azure-kusto-ingest>=4.2.0 azure-identity>=1.15.0 python-dotenv>=1.0.0 pandas>=2.0.0")
        sys.exit(1)

if __name__ == "__main__":
    main()