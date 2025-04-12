"""
Kusto query tools - Tools for executing KQL queries against Azure Kusto
"""

import json
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import importlib

from mcp.server.fastmcp import FastMCP, Context

def register_tools(mcp: FastMCP) -> None:
    """Register query-related tools"""
    
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
        
        # First validate the analysis_type before executing the query
        if analysis_type not in ["summary", "stats", "plot_ready"]:
            return "❌ Invalid analysis type. Supported types: summary, stats, plot_ready"
        
        if not query:
            return "❌ Query cannot be empty. Please provide a valid KQL query."
            
        success, result = await kusto_manager.execute_query(query)
        
        if not success:
            return f"❌ Query execution failed: {result}"
            
        try:
            if not hasattr(result, 'primary_results') or not result.primary_results:
                return "✅ Query executed successfully, but returned no results to analyze."
                
            df = pd.DataFrame(result.primary_results[0])
            
            if df.empty:
                return "✅ Query executed successfully, but returned no results to analyze."
                
            if analysis_type == "summary":
                # Provide basic summary of the data
                return f"""✅ Data Summary:

- Number of rows: {df.shape[0]}
- Number of columns: {df.shape[1]}
- Column names: {', '.join(df.columns)}

**Numeric Column Statistics:**
```
{df.describe().to_string()}
```

**Data Sample (First 5 rows):**
```
{df.head(5).to_string(index=False)}
```"""
            
            elif analysis_type == "stats":
                # Provide detailed statistics on numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if not numeric_cols:
                    return "✅ No numeric columns found for statistical analysis."
                    
                stats_df = df[numeric_cols].describe()
                correlation = None
                
                # Calculate correlation matrix if we have at least 2 numeric columns
                if len(numeric_cols) >= 2:
                    correlation = df[numeric_cols].corr().round(2).to_string()
                
                result = f"""✅ Statistical Analysis:

**Numeric Column Statistics:**
```
{stats_df.to_string()}
```

"""
                if correlation:
                    result += f"""
**Correlation Matrix:**
```
{correlation}
```
"""
                return result
                
            elif analysis_type == "plot_ready":
                # Just return the data in a format suitable for plotting
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
                
                return f"""✅ Plot-Ready Data Analysis:

**Data Structure:**
- Number of rows: {df.shape[0]}
- Numeric columns: {', '.join(numeric_cols) if numeric_cols else 'None'}
- Categorical columns: {', '.join(categorical_cols) if categorical_cols else 'None'}

**Sample Data (First 5 rows):**
```
{df.head(5).to_string(index=False)}
```

To plot this data, you can use the numeric columns for values and categorical columns for grouping or dimensions."""
                
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
        # This function does not actually execute the query, just analyzes the structure
        
        if not query:
            return "❌ Query cannot be empty. Please provide a valid KQL query."
            
        # Check for common optimization issues
        optimizations = []
        warnings = []
        
        # Clean the query for analysis (remove extra whitespace, normalize to lowercase)
        clean_query = query.strip().lower()
        query_parts = [part.strip() for part in clean_query.split('|')]
        
        # Check for select * pattern - but don't flag if there is already a project clause
        has_project = any('project ' in part and ' * ' not in part for part in query_parts)
        if (("| project *" in query or "| extend *" in query) or 
            (not has_project and "| project-away" not in query and len(query_parts) > 2)):
            optimizations.append("Consider explicitly selecting only the columns you need with '| project' instead of retrieving all columns")
            
        # Check for too many pipe operations
        if len(query_parts) > 10:
            warnings.append("This query has many pipe operations which may impact performance. Consider simplifying or using let statements for complex intermediate calculations")
        
        # Check for missing filters early in the query
        # Don't suggest early filters if we already have them
        has_early_filter = any('where ' in part for part in query_parts[:3]) or any('limit ' in part for part in query_parts[:3])
        if not has_early_filter and len(query_parts) > 2:
            optimizations.append("Consider adding filters ('where' clauses) early in your query to reduce the amount of data processed")
        
        # Check for missing time filter on time series data
        time_columns = ["timestamp", "time", "date", "datetime", "starttime", "endtime"]
        has_time_column_reference = any(time_col in clean_query for time_col in time_columns)
        has_time_filter = "ago(" in clean_query or "datetime" in clean_query
        if has_time_column_reference and not has_time_filter:
            warnings.append("This query appears to work with time data but doesn't have a time range filter. Consider adding a time filter for better performance")
        
        # Check for inefficient join patterns
        if "| join" in clean_query:
            join_parts = clean_query.split("| join")
            if len(join_parts) > 1 and "kind=" not in join_parts[1]:
                optimizations.append("Specify a join kind (e.g., 'kind=inner') to potentially improve join performance")
                
        # Check for sorting without limit
        has_sort = "sort by" in clean_query or "order by" in clean_query
        has_limit = "limit " in clean_query or "top " in clean_query
        if has_sort and not has_limit:
            optimizations.append("Queries with 'sort by' or 'order by' should usually include a 'limit' or 'top' clause to avoid sorting the entire result set")
        
        # Build response
        response = "## Query Optimization Analysis\n\n"
        
        if not optimizations and not warnings:
            response += "No obvious optimization issues detected in the query.\n\n"
        else:
            if optimizations:
                response += "### Suggested Optimizations:\n\n"
                for i, opt in enumerate(optimizations, 1):
                    response += f"{i}. {opt}\n"
                response += "\n"
                
            if warnings:
                response += "### Potential Issues:\n\n"
                for i, warn in enumerate(warnings, 1):
                    response += f"{i}. {warn}\n"
                response += "\n"
                
        # Add general best practices
        response += """### General KQL Best Practices:

1. Filter early and specifically to reduce data processing
2. Use time-based filters when working with time series data
3. Only select the columns you need
4. Use let statements for complex calculations or reused expressions
5. Use appropriate join types and join on indexed columns when possible
6. Be aware of the query time limit and data size limits

Your query:
```
"""
        response += query
        response += "\n```"
        
        return response