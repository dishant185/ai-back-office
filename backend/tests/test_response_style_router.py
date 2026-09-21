import pytest
from app.ai.response_style_router import ResponseStyle, determine_response_style

def test_direct_query_styles():
    assert determine_response_style("How many regions are covered?") == ResponseStyle.DIRECT
    assert determine_response_style("What is total revenue?") == ResponseStyle.DIRECT
    assert determine_response_style("What is the average order value?") == ResponseStyle.DIRECT
    assert determine_response_style("Who is the top sales rep?") == ResponseStyle.DIRECT
    assert determine_response_style("Count total customers") == ResponseStyle.DIRECT

def test_comparison_query_styles():
    assert determine_response_style("Compare North and South regions") == ResponseStyle.COMPARISON
    assert determine_response_style("How does East compare against West?") == ResponseStyle.COMPARISON
    assert determine_response_style("Difference between Q1 and Q2") == ResponseStyle.COMPARISON
    assert determine_response_style("versus last month") == ResponseStyle.COMPARISON

def test_table_query_styles():
    assert determine_response_style("Show regional breakdown as a table") == ResponseStyle.TABLE
    assert determine_response_style("Tabulate sales by department") == ResponseStyle.TABLE
    assert determine_response_style("Can you show this in a grid?") == ResponseStyle.TABLE
    assert determine_response_style("Show me a list of all products in table format") == ResponseStyle.TABLE

def test_summary_query_styles():
    assert determine_response_style("Summarize overall business performance") == ResponseStyle.SUMMARY
    assert determine_response_style("Give me an executive summary") == ResponseStyle.SUMMARY
    assert determine_response_style("Provide a quick overview of the dataset") == ResponseStyle.SUMMARY
    assert determine_response_style("Brief recap of recent results") == ResponseStyle.SUMMARY

def test_explanation_query_styles():
    assert determine_response_style("Why did customer churn increase?") == ResponseStyle.EXPLANATION
    assert determine_response_style("What caused the dip in sales?") == ResponseStyle.EXPLANATION
    assert determine_response_style("Explain why region North outperformed West") == ResponseStyle.EXPLANATION

def test_analysis_query_styles():
    assert determine_response_style("Analyze the root causes of supply delays") == ResponseStyle.ANALYSIS
    assert determine_response_style("Deep dive into customer retention drivers") == ResponseStyle.ANALYSIS
    assert determine_response_style("Provide a detailed analysis of performance") == ResponseStyle.ANALYSIS

def test_recommendation_query_styles():
    assert determine_response_style("What should we do to boost margin?") == ResponseStyle.RECOMMENDATION
    assert determine_response_style("Give me recommendations for inventory") == ResponseStyle.RECOMMENDATION
    assert determine_response_style("Suggest actionable steps to cut costs") == ResponseStyle.RECOMMENDATION

def test_trend_query_styles():
    assert determine_response_style("What is the revenue trend over time?") == ResponseStyle.TREND
    assert determine_response_style("How has trajectory evolved month over month?") == ResponseStyle.TREND
    assert determine_response_style("Show seasonal patterns in customer traffic") == ResponseStyle.TREND

def test_conversational_query_styles():
    assert determine_response_style("Hello there!") == ResponseStyle.CONVERSATIONAL
    assert determine_response_style("Hi") == ResponseStyle.CONVERSATIONAL
    assert determine_response_style("Thank you so much!") == ResponseStyle.CONVERSATIONAL
    assert determine_response_style("What can you do?") == ResponseStyle.CONVERSATIONAL

def test_unavailable_query_style():
    style = determine_response_style(
        "What is total profit margin?",
        context={"metrics": {"total_revenue": 100000}}
    )
    assert style == ResponseStyle.UNAVAILABLE
