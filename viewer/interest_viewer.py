from datetime import date, timedelta
import math
import statistics

import streamlit as st
import pandas as pd
import plotly.express as px

from planner.interest_rates.interest_and_inflation import INTEREST_AND_INFLATION
from planner.util import future_value

def get_index(year: int, month: int):
    first_index = INTEREST_AND_INFLATION[0]["year"] * 12 + (INTEREST_AND_INFLATION[0]["month"] - 1)
    return (year * 12 + (month - 1)) - first_index

def compound_annual_growth_rate(future_value: float, present_value: float, periods: int) -> float:
    return math.pow(future_value/present_value, (1/periods)) - 1

def view_interest():
    st.markdown("## Interest Viewer")
    min_date = date(
        INTEREST_AND_INFLATION[0]["year"],
        INTEREST_AND_INFLATION[0]["month"],
        1,
    )
    max_date = date(
        INTEREST_AND_INFLATION[-1]["year"],
        INTEREST_AND_INFLATION[-1]["month"],
        1,
    )
    start_date = st.date_input(
        "Start Date",
        min_value=min_date,
        max_value=max_date,
        value=min_date,
    )
    end_date = st.date_input(
        "End Date",
        min_value=min_date,
        max_value=max_date,
        value=max_date,
    )
    linear_rate_daily = st.number_input(
        "Linear % Yearly Interest Rate",
        min_value=0.0,
    ) / 100.0 / 365.0
    dates = []
    balances = []
    balance = 1.0
    current_date = start_date
    interests = []
    while current_date < end_date:
        dates.append(current_date)
        balances.append(balance)
        index = get_index(current_date.year, current_date.month)
        interest = INTEREST_AND_INFLATION[index]["value_pct_change_day"]
        interests.append(interest)
        balance += balance * interest
        current_date += timedelta(days=1)
    data = pd.DataFrame({
        "date": dates,
        "balance": balances
    })
    data["type"] = "historical"
    linear_balances = []
    balance = 1.0
    current_date = start_date
    while current_date < end_date:
        linear_balances.append(balance)
        balance += balance * linear_rate_daily
        current_date += timedelta(days=1)
    linear_data = pd.DataFrame({
        "date": dates,
        "balance": linear_balances
    })
    linear_data["type"] = "linear"
    data = pd.concat([data, linear_data])
    st.plotly_chart(px.scatter(
        data,
        x="date",
        y="balance",
        color="type",
    ))
    periods = (end_date.year * 12 + (end_date.month - 1)) - (start_date.year * 12 + (start_date.month - 1))
    st.write(f"Average Yearly Interest `{compound_annual_growth_rate(balances[-1], balances[0], periods) * 12.0 * 100.0}` %")
    mean_daily = statistics.mean(interests)
    st.write(f"Average daily interest: {mean_daily}")
    st.write(f"Average daily interest: {mean_daily * 365.0}")
    st.write(f"Future value: {future_value(1.00, mean_daily, len(interests)-1)}")
