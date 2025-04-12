# Azure Kusto MCP Server

A Model Context Protocol (MCP) server that connects to Azure Kusto, enabling AI assistants to explore data schemas and execute KQL queries.

## Features

- **Azure Kusto Integration**: Connect securely to Azure Kusto clusters
- **Schema Exploration**: Expose table schemas as resources for AI assistants
- **Query Execution**: Tools for running KQL queries and analyzing results
- **Data Analysis Assistance**: Built-in prompts for common data analysis tasks
- **VS Code Integration**: Configures connection details interactively within VS Code

## Requirements

- Python 3.9+
- Azure Kusto cluster access
- VS Code with GitHub Copilot or Copilot Chat extension (for MCP support)
- Required Python packages (installed automatically with setup script)

## Quick Setup (Recommended)

The easiest way to set up the MCP server with VS Code integration:

```
python setup-mcp.py
```

This script will:
1. Install all required dependencies
2. Create the necessary configuration for VS Code integration
3. Provide instructions for starting the server

## Manual Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/kusto-mcp-server.git
cd kusto-mcp-server
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. (Optional) Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
AZURE_KUSTO_CLUSTER=https://<your-cluster>.kusto.windows.net
AZURE_KUSTO_DATABASE=<your-database>
```

## VS Code Integration

To use the MCP server with VS Code:

1. Make sure you've run the setup script: `python setup-mcp.py`
2. Install the GitHub Copilot or Copilot Chat extension in VS Code
3. Open the Command Palette (Ctrl+Shift+P) 
4. Run "MCP: Start Server with Configuration"
5. Select "Azure Kusto MCP" from the list
6. Enter your Kusto cluster URL and database name when prompted

The MCP server will start and connect to your Copilot Chat session, allowing you to:
- Connect to your Kusto cluster using the `connect` tool
- Browse table schemas
- Execute queries
- Analyze data

## Running the Server Without VS Code

Start the MCP server directly with:
```
python -m src.kusto_mcp.server
```

If you haven't configured the connection in the `.env` file, the server will prompt you for connection details when needed.

## Authentication

This server uses Azure's DefaultAzureCredential for authentication, which supports:

1. Environment variables 
2. Managed Identity
3. Azure CLI credentials
4. Azure PowerShell credentials
5. Interactive browser authentication as a fallback

Make sure you're authenticated with at least one of these methods before connecting.

## Resource Types

The server exposes the following resources:

- `kusto/tables` - List of all tables in the current database
- `kusto/schema/{table_name}` - Schema for a specific table
- `kusto/sample` - Sample KQL query and explanation
- `kusto/connection` - Current connection information

## Tools

The following tools are available:

- `connect` - Connect to a Kusto cluster and database
- `connection_status` - Check the current connection status
- `execute_query` - Run a KQL query
- `analyze_data` - Execute a query and analyze the results
- `optimize_query` - Get suggestions for query optimization

## Prompts

Built-in prompts for common data analysis tasks:

- `time_series_analysis` - Analysis of time series data
- `cohort_analysis` - Retention and cohort studies
- `funnel_analysis` - User journey through event sequences
- `data_quality_check` - Data quality assessment

## Usage with AI Assistants

This MCP server is designed to work with AI assistants that support the Model Context Protocol. The server provides structured access to Azure Kusto data, allowing AI assistants to:

1. Browse available tables and schemas
2. Execute read-only KQL queries
3. Analyze query results
4. Provide guidance on data analysis

## Troubleshooting

If you encounter problems:

1. **Missing dependencies**: Run `python setup-mcp.py` to install all required packages
2. **Server won't start**: Check if another process is using the same port
3. **Connection issues**: Verify your Azure credentials and network connectivity 
4. **Import errors**: Make sure you're running the server from the project root directory

## Security Considerations

- The server uses Azure's DefaultAzureCredential for secure authentication
- Only users with appropriate permissions can access the Kusto cluster
- Credentials are never stored by the server itself

## License

MIT License