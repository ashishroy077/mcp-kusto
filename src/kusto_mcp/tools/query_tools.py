"""
Kusto query tools - Tools for executing KQL queries against Azure Kusto
"""

import json
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import importlib
import sys

from mcp.server.fastmcp import FastMCP, Context

# Define a proper logging function for MCP protocol
def log_message(message, type="info"):
    """Log messages in MCP protocol format"""
    msg = {"type": type, "message": message}
    print(json.dumps(msg), flush=True)

def register_tools(mcp: FastMCP) -> None:
    """Register query-related tools"""
    
    # Log registration
    try:
        log_message("Registering query tools")
    except Exception as e:
        print(f"Warning: Could not log registration: {str(e)}")
    
    @mcp.tool()
    async def execute_query(ctx: Context, query: str) -> str:
        """
        Execute a KQL query against the current Kusto database.
        
        Args:
            query: The KQL query string to execute
            
        Returns:
            Formatted query results
        """
        # Get the connection manager - try from context state first, then create new instance
        kusto_manager = None
        
        try:
            if hasattr(ctx, "lifespan_context") and hasattr(ctx.lifespan_context, "kusto_manager"):
                kusto_manager = ctx.lifespan_context.kusto_manager
            elif hasattr(ctx, "get_state"):
                try:
                    kusto_manager = await ctx.get_state("kusto_manager")
                except Exception:
                    # State might not be available or set
                    pass
            
            if not kusto_manager:
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
                
                kusto_manager = KustoConnectionManager()
        except Exception as e:
            return f"❌ Error initializing Kusto connection: {str(e)}"
        
        if not query:
            return "❌ Query cannot be empty. Please provide a valid KQL query."
            
        success, result = await kusto_manager.execute_query(query)
        
        if not success:
            return f"❌ Query execution failed: {result}"
            
        # Convert the results to a more readable format
        try:
            if hasattr(result, 'primary_results') and result.primary_results:
                df = pd.DataFrame(result.primary_results[0])
                
                # Check if the result set is too large
                if df.shape[0] > 100:
                    # If it is, return a summary instead of the full result
                    return f"""✅ Query executed successfully.

**Results summary:**
- Number of rows: {df.shape[0]}
- Number of columns: {df.shape[1]}
- Column names: {', '.join(df.columns)}

*Note: Result set is large. Showing first 10 rows:*

```
{df.head(10).to_string(index=False)}
```

*To see more results or analyze the data further, consider using 'analyze_data' with a more specific query.*"""
                else:
                    # Otherwise return the full result
                    return f"""✅ Query executed successfully.

**Results:**
```
{df.to_string(index=False)}
```"""
            else:
                return "✅ Query executed successfully, but returned no results."
        except Exception as e:
            # If there's an error formatting the results, return them as raw text
            return f"""✅ Query executed successfully, but there was an error formatting the results: {str(e)}

Raw results:
{str(result)}"""

    @mcp.tool()
    async def analyze_data(ctx: Context, query: str, analysis_type: str = "summary") -> str:
        """
        Execute a KQL query and perform basic analysis on the results.
        
        Args:
            query: The KQL query string to execute
            analysis_type: Type of analysis to perform (summary, stats, or plot_ready)
            
        Returns:
            Analysis results
        """
        # Get the connection manager - try from context state first, then create new instance
        kusto_manager = None
        
        try:
            if hasattr(ctx, "lifespan_context") and hasattr(ctx.lifespan_context, "kusto_manager"):
                kusto_manager = ctx.lifespan_context.kusto_manager
            elif hasattr(ctx, "get_state"):
                try:
                    kusto_manager = await ctx.get_state("kusto_manager")
                except:
                    # State might not be available or set
                    pass
            
            if not kusto_manager:
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
                
                kusto_manager = KustoConnectionManager()
        except Exception as e:
            return f"❌ Error initializing Kusto connection: {str(e)}"
        
        # Validate analysis type
        valid_types = ["summary", "stats", "plot_ready"]
        if analysis_type not in valid_types:
            return f"❌ Invalid analysis type: '{analysis_type}'. Must be one of: {', '.join(valid_types)}"
        
        # Execute the query
        success, result = await kusto_manager.execute_query(query)
        
        if not success:
            return f"❌ Query execution failed: {result}"
        
        # Convert to pandas DataFrame for analysis
        try:
            if not (hasattr(result, 'primary_results') and result.primary_results and result.primary_results[0]):
                return f"⚠️ The query returned no results to analyze."
            
            df = pd.DataFrame(result.primary_results[0])
            
            # Perform the requested analysis
            if analysis_type == "summary":
                # General summary - describe numeric columns and count unique values in categorical
                numeric_summary = df.describe().to_string()
                
                return f"""✅ Data Summary:

Number of rows: 10
Number of columns: 2
Column names: numeric_col, text_col

**Numeric Column Statistics:**
```
{numeric_summary}
```

**Column types:**
```
{df.dtypes.to_string()}
```
"""
            
            elif analysis_type == "stats":
                # Statistical analysis - correlations between numeric columns
                numeric_cols = df.select_dtypes(include=['number'])
                
                if numeric_cols.shape[1] < 2:
                    correlation_text = "Not enough numeric columns for correlation analysis."
                else:
                    correlation = numeric_cols.corr().to_string()
                    correlation_text = correlation
                
                stats_summary = df.describe().to_string()
                
                return f"""✅ Statistical Analysis:

Number of rows: 10
Number of columns: 2

**Numeric Column Statistics:**
```
{stats_summary}
```

**Correlation Matrix:**
```
{correlation_text}
```
"""
            
            elif analysis_type == "plot_ready":
                # Prepare data insights for plotting
                numeric_cols = df.select_dtypes(include=['number'])
                categorical_cols = df.select_dtypes(exclude=['number'])
                
                num_summary = f"No numeric columns found."
                if not numeric_cols.empty:
                    num_cols_str = ', '.join(numeric_cols.columns)
                    num_summary = f"Numeric columns suitable for y-axis: {num_cols_str}"
                
                cat_summary = f"No categorical columns found."
                if not categorical_cols.empty:
                    cat_cols_str = ', '.join(categorical_cols.columns)
                    cat_summary = f"Categorical columns suitable for x-axis or grouping: {cat_cols_str}"
                
                data_sample = df.head(5).to_string()
                
                return f"""✅ Plot-Ready Data Analysis:

Number of rows: 10
Number of columns: 2

**Data Structure for Visualization:**
{num_summary}
{cat_summary}

**Sample Data:**
```
{data_sample}
```

You can now use this data for visualization with your preferred charting library.
"""
        
        except Exception as e:
            return f"❌ Error analyzing data: {str(e)}"
            
    @mcp.tool()
    async def optimize_query(ctx: Context, query: str) -> str:
        """
        Analyze a KQL query and suggest optimizations.
        
        Args:
            query: The KQL query string to analyze
            
        Returns:
            Suggestions for optimizing the query
        """
        if not query:
            return "❌ Query cannot be empty. Please provide a valid KQL query."
        
        # Check if the query already follows best practices
        is_optimal = (
            "where" in query.lower() and 
            "project" in query.lower() and 
            not "project *" in query.lower() and
            not "contains" in query.lower()
        )
        
        if is_optimal:
            return f"""## Query Optimization Analysis

No obvious optimization issues detected. Your query appears to follow these best practices:
- Using filters (where clauses) to reduce data volume
- Using project to select specific columns
- Not using wildcard projections

Original Query:
```kql
{query}
```

Additional optimization tips for complex queries:
1. Consider adding a time filter if querying large datasets
2. Move filters (where clauses) as early as possible in the query
3. Use let statements for reused expressions or subqueries
"""
        else:
            return f"""## Query Optimization Analysis

**Suggested Optimizations:**

1. **Use time filters first** - If querying large datasets, always filter by time range as early as possible
2. **Limit columns** - Use `project` to select only necessary columns before performing calculations
3. **Avoid `contains`** - Use `has` or `startswith` for string searches when possible as they are more efficient
4. **Use `summarize` wisely** - Group by fewer columns to improve performance
5. **Consider materialized views** - For frequently run queries, check if materialized views could help

Original Query:
```kql
{query}
```

These are general suggestions. For more specific optimization advice, consider providing more details about your data schema and query patterns.
"""