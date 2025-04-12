"""
Kusto analysis prompts - Guided templates for common data analysis tasks
"""

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import base

def register_prompts(mcp: FastMCP) -> None:
    """Register data analysis prompts"""

    @mcp.prompt()
    def time_series_analysis(table_name: str, time_column: str, measure_column: str, filter_condition: str = "") -> list[base.Message]:
        """
        Create a time series analysis for a specified table, time column, and measure.
        
        Args:
            table_name: The name of the Kusto table
            time_column: The column containing timestamps
            measure_column: The column to measure/aggregate
            filter_condition: Optional filter condition (without 'where')
        """
        filter_part = f"| where {filter_condition}" if filter_condition else ""
        
        query_parts = [
            f"""// Time series analysis for {measure_column} in {table_name}
{table_name}
{filter_part}
| where isnotnull({time_column}) and isnotnull({measure_column})
| summarize avg_{measure_column} = avg({measure_column}), 
           min_{measure_column} = min({measure_column}), 
           max_{measure_column} = max({measure_column}), 
           count_{measure_column} = count() by bin({time_column}, 1h)
| sort by {time_column} asc""",
            
            f"""// Detect anomalies in time series
{table_name}
{filter_part}
| where isnotnull({time_column}) and isnotnull({measure_column})
| make-series value = avg({measure_column}) on {time_column} from ago(7d) to now() step 1h
| extend anomalies = series_decompose_anomalies(value)
| mv-expand {time_column} to typeof(datetime), value to typeof(double), anomalies to typeof(double)
| where anomalies != 0
| project {time_column}, value, anomalies"""
        ]
        
        return [
            base.UserMessage(f"I need to analyze the time series data for '{measure_column}' in the '{table_name}' table."),
            base.AssistantMessage("I'll help you analyze this time series data. Here are some queries you can use:"),
            base.UserMessage("Query 1: Basic time series analysis"),
            base.AssistantMessage(query_parts[0]),
            base.UserMessage("Can you also help me detect anomalies in this data?"),
            base.AssistantMessage("Certainly! Here's a query to detect anomalies:"),
            base.AssistantMessage(query_parts[1]),
            base.UserMessage("What insights should I look for in these results?"),
            base.AssistantMessage("""When analyzing the time series results, look for:

1. **Patterns and trends**: Are there daily, weekly, or seasonal patterns?
2. **Anomalies and outliers**: Points that deviate significantly from the pattern
3. **Sudden changes**: Sharp increases or decreases that might indicate events
4. **Missing data**: Gaps in the time series that might affect your analysis
5. **Correlations**: How this measure relates to other business metrics

For anomaly detection results, focus on:
1. The timestamp when anomalies occurred
2. The magnitude of the anomaly (how far from normal)
3. Potential external factors that coincide with the anomalies

Use the `analyze_data` tool with these queries to get statistical summaries.
""")
        ]

    @mcp.prompt()
    def cohort_analysis(table_name: str, cohort_column: str, date_column: str, event_column: str = None) -> list[base.Message]:
        """
        Create a cohort analysis for retention/churn studies.
        
        Args:
            table_name: The name of the Kusto table
            cohort_column: The column that identifies the cohort (e.g., user_id)
            date_column: The column containing event dates
            event_column: Optional column for filtering specific events
        """
        event_filter = f"| where {event_column} == 'desired_event'" if event_column else ""
        
        query = f"""// Cohort retention analysis
let cohorts = {table_name}
{event_filter}
| summarize min_date = min({date_column}) by {cohort_column}
| summarize count() by cohort_date = startofweek(min_date);
let cohort_activities = {table_name}
{event_filter}
| join kind=inner (
    {table_name}
    | summarize min_date = min({date_column}) by {cohort_column}
) on {cohort_column}
| extend weeks = datetime_diff('week', {date_column}, min_date)
| where weeks >= 0
| summarize users = count_distinct({cohort_column}) by cohort_date = startofweek(min_date), weeks;
cohort_activities
| join kind=inner cohorts on cohort_date
| project cohort_date, weeks, users, percentage = (users * 100) / count_
| sort by cohort_date asc, weeks asc"""
        
        return [
            base.UserMessage(f"I want to perform cohort analysis on the '{table_name}' table using '{cohort_column}' to identify cohorts."),
            base.AssistantMessage("I'll help you set up a cohort analysis. This will show how groups of users/entities behave over time."),
            base.UserMessage("What query should I use for cohort retention analysis?"),
            base.AssistantMessage("Here's a query for cohort retention analysis:"),
            base.AssistantMessage(query),
            base.UserMessage("How do I interpret these results?"),
            base.AssistantMessage("""When interpreting cohort analysis results:

1. **Diagonal reading**: Each row represents a cohort, and columns show their behavior over time
2. **Retention rate**: The percentage of users who return in subsequent periods
3. **Patterns across cohorts**: Compare how different cohorts behave over time
4. **Churn analysis**: Look at where the significant drops occur
5. **Lifecycle insights**: Identify critical periods where you might lose users

Key metrics to focus on:
- Initial retention (Week 1) - immediate drop-off
- Long-term retention plateaus - your loyal base
- Cohort differences - whether newer cohorts perform better or worse than older ones

You might want to visualize this data as a heatmap for easier interpretation.
""")
        ]

    @mcp.prompt()
    def funnel_analysis(table_name: str, user_id_column: str, event_column: str, timestamp_column: str, funnel_steps: list) -> list[base.Message]:
        """
        Create a funnel analysis to track user journey through a sequence of events.
        
        Args:
            table_name: The name of the Kusto table
            user_id_column: Column that identifies the user
            event_column: Column that contains the event name/type
            timestamp_column: Column containing the event timestamp
            funnel_steps: List of event names in order of the funnel
        """
        steps = "', '".join(funnel_steps)
        
        query = f"""// Funnel analysis
let funnel_events = dynamic(['{steps}']);
let total_users = {table_name}
| where {event_column} == funnel_events[0]
| summarize count_distinct({user_id_column});
{table_name}
| where {event_column} in (funnel_events)
| summarize timestamp = min({timestamp_column}) by {user_id_column}, {event_column}
| extend step = array_index_of(funnel_events, {event_column})
| where step >= 0
| summarize reached_step = max(step) by {user_id_column}
| summarize users = count() by reached_step
| extend step_name = funnel_events[reached_step]
| extend total_users = toscalar(total_users)
| extend conversion_rate = (users * 100.0) / total_users
| sort by reached_step asc
| project step = reached_step + 1, 
         step_name, 
         users, 
         percentage_of_total = conversion_rate,
         drop_off = iff(reached_step > 0, lag(users) - users, 0),
         drop_off_rate = iff(reached_step > 0, (lag(users) - users) * 100.0 / lag(users), 0)"""
        
        return [
            base.UserMessage(f"I need to analyze the conversion funnel through these steps: {', '.join(funnel_steps)}"),
            base.AssistantMessage("I'll help you create a funnel analysis to track how users progress through those steps."),
            base.UserMessage("What KQL query should I use for the funnel analysis?"),
            base.AssistantMessage("Here's a query for funnel analysis:"),
            base.AssistantMessage(query),
            base.UserMessage("What insights should I look for in the funnel analysis?"),
            base.AssistantMessage("""When analyzing funnel results, focus on:

1. **Overall conversion rate**: Percentage of users who complete the entire funnel
2. **Step-by-step drop-off**: Where you lose the most users
3. **Critical blockage points**: Steps with unusually high drop-off rates
4. **Time between steps**: How long it takes users to move from one step to another
5. **Segment comparisons**: How different user groups perform in the funnel

Key questions to answer:
- Which step has the highest drop-off rate?
- What percentage of users complete the entire funnel?
- Are there any unexpected patterns in how users move through the funnel?
- How does this funnel performance compare to previous periods?

Consider enhancing this analysis by:
- Adding time segmentation (day/week/month)
- Filtering by user attributes
- Comparing different user segments
""")
        ]

    @mcp.prompt()
    def data_quality_check(table_name: str) -> list[base.Message]:
        """
        Create a data quality assessment for a Kusto table.
        
        Args:
            table_name: The name of the table to analyze
        """
        queries = [
            f"""// Check for completeness (missing values)
{table_name}
| summarize column_stats = bag_pack(
    "total_rows", count(),
    "columns", pack_all()
)
| mv-expand col_name = bag_keys(column_stats.columns)
| extend nulls = column_stats.columns[tostring(col_name)].nulls
| extend null_percentage = round((nulls * 100.0) / column_stats.total_rows, 2)
| project column = tostring(col_name), 
         total_rows = column_stats.total_rows,
         null_count = nulls,
         null_percentage
| sort by null_percentage desc""",

            f"""// Check for duplicates
{table_name}
| summarize row_count = count() by *
| where row_count > 1
| count""",

            f"""// Check value distributions
{table_name}
| sample 1000
| evaluate pivot(column_ifexists, values_builder(count()))"""
        ]
        
        return [
            base.UserMessage(f"I need to check the data quality of the '{table_name}' table."),
            base.AssistantMessage("I'll help you assess the data quality. Here are some queries for different quality dimensions:"),
            base.UserMessage("Can you give me a query to check for missing values?"),
            base.AssistantMessage("Here's a query to check for completeness (missing values):"),
            base.AssistantMessage(queries[0]),
            base.UserMessage("How about checking for duplicates?"),
            base.AssistantMessage("Here's a query to check for duplicates:"),
            base.AssistantMessage(queries[1]),
            base.UserMessage("And how can I check the distribution of values?"),
            base.AssistantMessage("Here's a query to examine value distributions:"),
            base.AssistantMessage(queries[2]),
            base.UserMessage("What should I do with these results?"),
            base.AssistantMessage("""When assessing data quality, consider these aspects:

1. **Completeness**: Look for columns with high null percentages
   - Are these expected missing values?
   - Does this affect your analysis?
   - Consider strategies for handling missing data (imputation, filtering, etc.)

2. **Uniqueness**: Examine duplicate records
   - Are duplicates expected in your data model?
   - Could duplicates skew your analysis results?
   - Consider deduplication strategies if needed

3. **Consistency**: Review value distributions
   - Look for unexpected values or patterns
   - Check for outliers or impossible values
   - Verify that values match your business rules

4. **Timeliness**: If your data has timestamps
   - Check for gaps in time series data
   - Verify that data is current
   - Look for unusual patterns in data freshness

Based on these findings, you might need to:
- Clean the data before analysis
- Add data quality monitoring
- Address upstream issues causing quality problems
- Document limitations in your analysis
""")
        ]