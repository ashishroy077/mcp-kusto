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

## Creating mcp.json Configuration File

The `mcp.json` file is required to configure the MCP server with VS Code. If you're setting up manually or the setup script didn't create this file, follow these steps:

1. Create a new file named `mcp.json` in the `.vscode` directory of your workspace (create this directory if it doesn't exist)
2. Add the following content to the file:

```json
{
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
      "command": "${command:python.interpreterPath}",
      "args": ["${workspaceFolder}/src/kusto_mcp/server.py"],
      "env": {
        "AZURE_KUSTO_CLUSTER": "${input:kusto-cluster}",
        "AZURE_KUSTO_DATABASE": "${input:kusto-database}",
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

3. If needed, customize the configuration:
   - Change the `command` if you need to use a specific Python interpreter path
   - Modify the `args` if your server script is located elsewhere
   - Add additional environment variables if required
   - Note that `${workspaceFolder}` and `${command:python.interpreterPath}` are VS Code variables that will be automatically replaced with the appropriate paths

This configuration includes input prompts that will ask for your Kusto cluster URL and database name each time you start the server, making it easy to switch between different databases.

## VS Code Integration

To use the MCP server with VS Code:

1. Make sure you've run the setup script: `python setup-mcp.py` or manually created the `mcp.json` file
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

## Tools Usage Guide

The Kusto MCP server provides several tools for interacting with Azure Kusto. Here's how to use each tool effectively:

### Connect Tool

The `connect` tool establishes a connection to an Azure Kusto cluster and database.

**Usage in Copilot Chat:**
```
I need to connect to my Kusto cluster
```

This tool will prompt you for:
- The cluster URL (e.g., https://yourcluster.kusto.windows.net)
- The database name

Authentication is handled automatically via Azure's DefaultAzureCredential.

**Example:**
```
Connect to the Kusto database named "MyDatabase" on the cluster "analytics.kusto.windows.net"
```

### Connection Status Tool

The `connection_status` tool shows your current connection details.

**Usage in Copilot Chat:**
```
Check my current Kusto connection
```

**Example Output:**
```
✅ Connected to Azure Kusto.
        
- **Cluster**: https://analytics.kusto.windows.net
- **Database**: MyDatabase
```

### Execute Query Tool

The `execute_query` tool runs KQL queries against your connected database.

**Usage in Copilot Chat:**
```
Run this KQL query: <your query here>
```

**Example:**
```
Run this KQL query: StormEvents | where State == "FLORIDA" | take 10
```

For large result sets (>100 rows), the tool will return a summary and the first 10 rows.

### Analyze Data Tool

The `analyze_data` tool executes a query and performs analysis on the results.

**Usage in Copilot Chat:**
```
Analyze this query: <your query here>
```

You can specify an analysis type:
- `summary` (default): Basic statistics about the data
- `stats`: Detailed statistical analysis including correlations
- `plot_ready`: Information to help visualize the data

**Example:**
```
Analyze this query with stats analysis: StormEvents | summarize count() by State | top 10 by count_
```

### Optimize Query Tool

The `optimize_query` tool provides suggestions to improve your KQL queries.

**Usage in Copilot Chat:**
```
Optimize this KQL query: <your query here>
```

**Example:**
```
Optimize this KQL query: 
StormEvents
| project *
| where StartTime > ago(7d)
| sort by StartTime desc
```

## Advanced Usage Scenarios

### Exploring Table Schemas

To explore available tables and their schemas:

```
What tables are available in this database?
```

To examine a specific table's schema:

```
Show me the schema for the StormEvents table
```

### Time Series Analysis

For time-based data analysis:

```
Help me analyze time trends in the StormEvents table using the StartTime column
```

### Correlation Analysis

To find relationships between columns:

```
Find correlations between DamageProperty and DeathsDirect in the StormEvents table
```

### Data Quality Checks

To verify data quality:

```
Check for null values and outliers in the StormEvents table
```

### Query Construction Step-by-Step

For complex queries, you can ask for guidance:

```
I need to build a query that shows storm events by state, with damage amounts, limited to the top 10 most expensive events. Can you help me construct this?
```

## Best Practices

1. **Always connect first**: Use the `connect` tool before attempting to run queries
2. **Verify connections**: Use the `connection_status` tool if you're unsure about your connection state
3. **Start with small queries**: Use `take` or `limit` operators to test queries before running on large datasets
4. **Use analysis tools**: The `analyze_data` tool provides valuable insights with minimal effort
5. **Ask for optimization**: Use the `optimize_query` tool for long-running or complex queries

## KQL Query Examples

Here are some example KQL queries to get you started:

```kql
// Simple filtering
StormEvents 
| where State == "FLORIDA" 
| take 10

// Aggregation
StormEvents
| summarize EventCount=count() by State
| order by EventCount desc
| take 10

// Time filtering
StormEvents
| where StartTime > ago(30d)
| summarize EventCount=count() by bin(StartTime, 1d)
| render timechart

// Join example
StormEvents
| where EventType == "Tornado"
| join (
    StormEvents 
    | where EventType == "Flood"
    | project State, FloodTime=StartTime
) on State
| project State, TornadoTime=StartTime, FloodTime
| take 10
```

## Troubleshooting MCP Configuration

If you're having issues with the MCP configuration:

1. **Missing mcp.json**: Create the file manually in the `.vscode` directory as described above
2. **Configuration not showing**: Ensure the `mcp.json` file is properly formatted and located in the `.vscode` directory
3. **Server not connecting**: Check that the hostname and port specified in the `mcp.json` file are available
4. **Copilot not detecting server**: Restart VS Code after creating or modifying the `mcp.json` file

## Troubleshooting Common Issues

In addition to the general troubleshooting tips mentioned earlier, here are specific solutions for common tool issues:

### Connect Tool Issues

- **Error: "Failed to connect"**: Verify your Azure credentials are valid and you have access to the specified cluster and database
- **Timeout errors**: Check your network connection and firewall settings
- **Authentication failures**: Ensure you're logged into Azure with `az login` or have valid environment credentials

### Query Execution Issues

- **Timeout on large queries**: Add filters or time constraints to reduce the data volume
- **Syntax errors**: Use the `optimize_query` tool to check and fix your query syntax
- **Missing columns**: Verify column names using schema exploration before querying

### Data Analysis Issues

- **Empty analysis results**: Ensure your query returns data before analyzing
- **Correlation errors**: Check that your data contains at least two numeric columns for correlation analysis
- **Visualization preparation**: For `plot_ready` analysis, include both categorical and numeric columns for best results

## Usage with AI Assistants

This MCP server is designed to work with AI assistants that support the Model Context Protocol. The server provides structured access to Azure Kusto data, allowing AI assistants to:

1. Browse available tables and schemas
2. Execute read-only KQL queries
3. Analyze query results
4. Provide guidance on data analysis

## Security Considerations

- The server uses Azure's DefaultAzureCredential for secure authentication
- Only users with appropriate permissions can access the Kusto cluster
- Credentials are never stored by the server itself

## License

MIT License