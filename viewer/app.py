from pathlib import Path

import streamlit as st
import plotly.express as px
import pandas as pd

from planner.config_reading import read_configuration
from planner import Simulation

from simulation_editor import edit_simulation

""" # Plan Results Viewer"""

run_options = ["Previous", "Live"]
run_type = st.radio(
    "Results Type",
    options=run_options
)
live_operation = run_type == run_options[1]

if live_operation:
    if st.checkbox("Auto-run"):
        run = True
    else:
        run = st.button("Run Simulation")
    if run:
        configuration = read_configuration([], Path("../payne_private/all_payne.yml"))
        with st.spinner('Running simulation...'):
            simulation = edit_simulation(Simulation(**configuration))
            #if st.button("Run Simulation"):
            days, asset_states, action_logs, tax_data, state_tax_data, error_raised = simulation.run()
            # else:
            #     st.stop()
            if error_raised is not None:
                st.error(error_raised)
            else:
                st.success("Simulation ran to completion!")
            st.info(f"Simulated {days} days")
    else:
        st.stop()
else:
    st.button("Refresh")

if live_operation:
    data = pd.DataFrame(asset_states)
else:
    data = pd.read_csv("../output.csv")
if st.checkbox("Filter Assets"):
    selectable_assets = data["name"].unique()
    selected_assets = st.multiselect(
        "Filtered Assets",
        options=selectable_assets
    )
    data = data.loc[data["name"].isin(selected_assets)]
st.plotly_chart(px.line(
    data,
    x="date",
    y="balance",
    color="name",
))
if live_operation:
    data = pd.DataFrame(asset_states)
else:
    data = pd.read_csv("../output.csv")
data["asset"] = data["balance"] > 0.0
nw_data = data.groupby(["date", "asset"]).sum().reset_index(drop=False)
nw_data["type"] = "liability"
nw_data.loc[nw_data["asset"], "type"] = "asset"
total_data = data.groupby(["date"]).sum().reset_index(drop=False)
total_data["type"] = "net_worth"
category_data = data.groupby(["date", "category"]).sum().reset_index(drop=False)
category_data["type"] = category_data["category"]
nw_data = pd.concat([total_data, nw_data, category_data])
st.plotly_chart(px.line(
    nw_data,
    x="date",
    y="balance",
    color="type",
))

def display_income_or_expenses(data, expenses: bool = True, live_operation: bool = False):
    if live_operation:
        data = pd.DataFrame(action_logs)
        data["date"] = pd.to_datetime(data["date"])
        data["amount"] = data["amount"].astype(float)
    else:
        data = pd.read_csv("../changes.csv", parse_dates=["date"])
    data = data.loc[~data["asset_maturity"], :]
    if expenses:
        data = data.loc[data["amount"] < 0.00, :]
        account_label = "Sources"
        data_type = "Expenses"
    else:
        data = data.loc[data["amount"] > 0.00, :]
        account_label = "Destinations"
        data_type = "Income"
    account_options = data["changed_item"].unique()
    selected_accounts = st.multiselect(
        f"Displayed Account {account_label}",
        account_options,
        default=account_options,
    )
    data["year"] = data["date"].dt.year
    data = data.drop(["date"], axis="columns")
    data = data.loc[data["changed_item"].isin(selected_accounts), :]
    data = data.groupby(["year", "category"]).sum().reset_index(drop=False)
    st.plotly_chart(px.bar(
        data,
        x="year",
        y="amount",
        color="category",
    ))

    selected_year = int(st.selectbox(
        f"{data_type} for Selected Year",
        options=data["year"].unique(),
    ))
    pie_data = data.loc[data["year"] == selected_year, :]
    pie_data["abs_amount"] = pie_data["amount"].abs()
    st.plotly_chart(px.pie(
        pie_data,
        names="category",
        values="abs_amount",
    ))

if st.checkbox("Show Expenses", value=True):
    display_income_or_expenses(data)

if st.checkbox("Show Income", value=True):
    display_income_or_expenses(data, expenses=False)

if st.checkbox("Show Fed Taxes", value=True):
    if live_operation:
        data = pd.DataFrame(tax_data)
    else:
        data = pd.read_csv("../yearly_fed_taxes.csv")
    data = pd.melt(
        data,
        id_vars=["year"],
        value_vars=[d for d in data.columns if d != "year"],
    )
    st.plotly_chart(px.line(
        data,
        x="year",
        y="value",
        color="variable",
    ))
if st.checkbox("Show State Taxes", value=True):
    if live_operation:
        data = pd.DataFrame(state_tax_data)
    else:
        data = pd.read_csv("../yearly_state_taxes.csv")
    data = pd.melt(
        data,
        id_vars=["year"],
        value_vars=[d for d in data.columns if d != "year"],
    )
    st.plotly_chart(px.line(
        data,
        x="year",
        y="value",
        color="variable",
    ))
if st.checkbox("Log Viewer"):
    if st.checkbox("Filter States"):
        data = pd.read_csv("../output.csv")
        selected_name = st.selectbox(
            "Account to filter on",
            options=data["name"].unique()
        )
        st.write(data[data["name"] == selected_name])
    if st.checkbox("Filter Changes"):
        data = pd.read_csv("../changes.csv")
        selected_name = st.selectbox(
            "Account to filter",
            options=data["changed_item"].unique()
        )
        st.write(data[data["changed_item"] == selected_name])