"""
Tests for the Kusto query tools.
"""

import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch

from src.kusto_mcp.tools.query_tools import register_tools


class MockFastMCP:
    """Mock FastMCP for testing tool registration."""
    
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


@pytest.fixture
def mock_mcp():
    """Create a mock MCP instance."""
    return MockFastMCP()


@pytest.fixture
def register_query_tools(mock_mcp):
    """Register query tools with mock MCP."""
    register_tools(mock_mcp)
    return mock_mcp


@pytest.mark.asyncio
async def test_execute_query_success(register_query_tools, mock_context):
    """Test execute_query tool with successful query."""
    # Setup test data
    sample_data = [{"col1": "value1", "col2": 123}]
    mock_result = MagicMock()
    mock_result.primary_results = [sample_data]
    
    # Configure the mock
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    # Execute the tool function
    result = await register_query_tools.tools["execute_query"](mock_context, "test query")
    
    # Verify the results
    assert "✅ Query executed successfully" in result
    assert "col1" in result
    assert "col2" in result
    assert "value1" in result
    mock_context.lifespan_context.kusto_manager.execute_query.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_execute_query_empty(register_query_tools, mock_context):
    """Test execute_query tool with empty query."""
    result = await register_query_tools.tools["execute_query"](mock_context, "")
    
    assert "❌ Query cannot be empty" in result
    mock_context.lifespan_context.kusto_manager.execute_query.assert_not_called()


@pytest.mark.asyncio
async def test_execute_query_failure(register_query_tools, mock_context):
    """Test execute_query tool with failed query."""
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (False, "Error message")
    
    result = await register_query_tools.tools["execute_query"](mock_context, "test query")
    
    assert "❌ Query execution failed" in result
    assert "Error message" in result


@pytest.mark.asyncio
async def test_execute_query_large_result(register_query_tools, mock_context):
    """Test execute_query tool with a large result set."""
    # Create a large result set (more than 100 rows)
    large_data = [{"col1": f"value{i}", "col2": i} for i in range(150)]
    mock_result = MagicMock()
    mock_result.primary_results = [large_data]
    
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    with patch("pandas.DataFrame.to_string", return_value="formatted_dataframe"):
        result = await register_query_tools.tools["execute_query"](mock_context, "test query")
    
    assert "✅ Query executed successfully" in result
    assert "Number of rows: 150" in result
    assert "Result set is large" in result
    assert "first 10 rows" in result.lower()


@pytest.mark.asyncio
async def test_analyze_data_summary(register_query_tools, mock_context):
    """Test analyze_data tool with summary analysis type."""
    sample_data = [{"numeric_col": 123, "text_col": "value"} for _ in range(10)]
    mock_result = MagicMock()
    mock_result.primary_results = [sample_data]
    
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    with patch("pandas.DataFrame.describe", return_value=pd.DataFrame({"numeric_col": [10, 123, 123, 0]})), \
         patch("pandas.DataFrame.to_string", return_value="summarized_data"):
        result = await register_query_tools.tools["analyze_data"](mock_context, "test query")
    
    assert "✅ Data Summary" in result
    assert "Number of rows: 10" in result
    assert "Numeric Column Statistics" in result
    mock_context.lifespan_context.kusto_manager.execute_query.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_analyze_data_stats(register_query_tools, mock_context):
    """Test analyze_data tool with stats analysis type."""
    sample_data = [{"numeric_col": 123, "numeric_col2": 456} for _ in range(10)]
    mock_result = MagicMock()
    mock_result.primary_results = [sample_data]
    
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    with patch("pandas.DataFrame.describe", return_value=pd.DataFrame()), \
         patch("pandas.DataFrame.corr", return_value=pd.DataFrame()), \
         patch("pandas.DataFrame.to_string", return_value="correlation_data"):
        result = await register_query_tools.tools["analyze_data"](mock_context, "test query", "stats")
    
    assert "✅ Statistical Analysis" in result
    assert "Numeric Column Statistics" in result
    assert "Correlation Matrix" in result


@pytest.mark.asyncio
async def test_analyze_data_plot_ready(register_query_tools, mock_context):
    """Test analyze_data tool with plot_ready analysis type."""
    sample_data = [{"numeric_col": 123, "category_col": "category"} for _ in range(10)]
    mock_result = MagicMock()
    mock_result.primary_results = [sample_data]
    
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    with patch("pandas.DataFrame.select_dtypes", side_effect=[
        pd.DataFrame({"numeric_col": [123] * 10}),  # For numeric columns
        pd.DataFrame({"category_col": ["category"] * 10})  # For categorical columns
    ]), patch("pandas.DataFrame.to_string", return_value="sample_data"):
        result = await register_query_tools.tools["analyze_data"](mock_context, "test query", "plot_ready")
    
    assert "✅ Plot-Ready Data Analysis" in result
    assert "Data Structure" in result
    assert "numeric_col" in result
    assert "category_col" in result


@pytest.mark.asyncio
async def test_analyze_data_invalid(register_query_tools, mock_context):
    """Test analyze_data tool with invalid analysis type."""
    result = await register_query_tools.tools["analyze_data"](mock_context, "test query", "invalid")
    
    assert "❌ Invalid analysis type" in result


@pytest.mark.asyncio
async def test_analyze_data_empty_result(register_query_tools, mock_context):
    """Test analyze_data tool with empty result."""
    mock_result = MagicMock()
    mock_result.primary_results = [[]]
    
    mock_context.lifespan_context.kusto_manager.execute_query.return_value = (True, mock_result)
    
    result = await register_query_tools.tools["analyze_data"](mock_context, "test query")
    
    assert "returned no results to analyze" in result


@pytest.mark.asyncio
async def test_optimize_query(register_query_tools, mock_context):
    """Test optimize_query tool."""
    # Test with a query that has optimization opportunities
    query = """
    StormEvents
    | project *
    | sort by StartTime
    | join Events on EventId
    | where State == 'FLORIDA'
    """
    
    result = await register_query_tools.tools["optimize_query"](mock_context, query)
    
    assert "Query Optimization Analysis" in result
    assert "Suggested Optimizations" in result
    assert "project" in result
    assert "sort by" in result or "order by" in result
    assert "join" in result


@pytest.mark.asyncio
async def test_optimize_query_no_issues(register_query_tools, mock_context):
    """Test optimize_query with a query that has no obvious issues."""
    query = """
    StormEvents
    | where StartTime > ago(1h)
    | where State == 'FLORIDA'
    | project EventId, StartTime, EndTime, State
    | limit 100
    """
    
    result = await register_query_tools.tools["optimize_query"](mock_context, query)
    
    assert "No obvious optimization issues detected" in result