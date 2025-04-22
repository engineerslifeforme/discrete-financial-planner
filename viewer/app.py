from pathlib import Path

import streamlit as st
import plotly.express as px
import pandas as pd

from tax_viewer import view_taxes
from interest_viewer import view_interest

asset_data = pd.read_csv("../asset_log.csv")
action_data = pd.read_csv("../action_log.csv", parse_dates=["date"])

""" # Plan Results Viewer"""

modes = [
    "Summary",
    "Taxes",
    "Interest",
]

st.sidebar.button("Refresh")
mode = st.sidebar.radio(
    "Viewer Mode",
    options=modes,
)

if mode == modes[1]:
    view_taxes(action_data)
elif mode == modes[2]:
    view_interest()
else:
    if st.checkbox("Filter Assets"):
        selectable_assets = asset_data["name"].unique()
        selected_assets = st.multiselect(
            "Filtered Assets",
            options=selectable_assets
        )
        asset_data = asset_data.loc[asset_data["name"].isin(selected_assets)]
    st.plotly_chart(px.line(
        asset_data,
        x="date",
        y="balance",
        color="name",
    ))
    asset_data["asset"] = asset_data["balance"] > 0.0
    nw_data = asset_data.groupby(["date", "asset"]).sum().reset_index(drop=False)
    nw_data["type"] = "liability"
    nw_data.loc[nw_data["asset"], "type"] = "asset"
    total_data = asset_data.groupby(["date"]).sum().reset_index(drop=False)
    total_data["type"] = "net_worth"
    category_data = asset_data.groupby(["date", "category"]).sum().reset_index(drop=False)
    category_data["type"] = category_data["category"]
    nw_data = pd.concat([total_data, nw_data, category_data])
    st.plotly_chart(px.line(
        nw_data,
        x="date",
        y="balance",
        color="type",
    ))

    def display_income_or_expenses(data, expenses: bool = True):
        data = pd.read_csv("../action_log.csv", parse_dates=["date"])
        if expenses:
            data = data.loc[data["amount"] < 0.00, :]
            account_label = "Sources"
            data_type = "Expenses"
        else:
            data = data.loc[data["amount"] > 0.00, :]
            account_label = "Destinations"
            data_type = "Income"
        account_options = data["asset_name"].unique()
        selected_accounts = st.multiselect(
            f"Displayed Account {account_label}",
            account_options,
            default=account_options,
        )
        color_field = st.radio(f"{data_type} Color Field", options=["category", "asset_name", "description"])
        data["year"] = data["date"].dt.year
        data = data.drop(["date"], axis="columns")
        data = data.loc[data["asset_name"].isin(selected_accounts), :]
        data = data.groupby(["year", color_field]).sum().reset_index(drop=False)
        st.plotly_chart(px.bar(
            data,
            x="year",
            y="amount",
            color=color_field,
        ))

        selected_year = int(st.selectbox(
            f"{data_type} for Selected Year",
            options=data["year"].unique(),
        ))
        year_filtered = data.loc[data["year"] == selected_year, :]
        year_filtered["abs_amount"] = year_filtered["amount"].abs()
        st.plotly_chart(px.pie(
            year_filtered,
            names=color_field,
            values="abs_amount",
        ))
        if st.checkbox("Show Year Totals Table"):
            st.write(year_filtered[["description", "amount"]])
            #st.write(year_filtered)

    if st.checkbox("Show Expenses", value=True):
        display_income_or_expenses(asset_data)

    if st.checkbox("Show Income", value=True):
        display_income_or_expenses(asset_data, expenses=False)

    if st.checkbox("Show Fed Taxes", value=True):
        asset_data = pd.read_csv("../yearly_fed_taxes.csv")
        asset_data = pd.melt(
            asset_data,
            id_vars=["year"],
            value_vars=[d for d in asset_data.columns if d != "year"],
        )
        st.plotly_chart(px.line(
            asset_data,
            x="year",
            y="value",
            color="variable",
        ))
    if st.checkbox("Show State Taxes", value=True):
        if live_operation:
            asset_data = pd.DataFrame(state_tax_data)
        else:
            asset_data = pd.read_csv("../yearly_state_taxes.csv")
        asset_data = pd.melt(
            asset_data,
            id_vars=["year"],
            value_vars=[d for d in asset_data.columns if d != "year"],
        )
        st.plotly_chart(px.line(
            asset_data,
            x="year",
            y="value",
            color="variable",
        ))
    if st.checkbox("Log Viewer"):
        if st.checkbox("Filter States"):
            asset_data = pd.read_csv("../output.csv")
            selected_name = st.selectbox(
                "Account to filter on",
                options=asset_data["name"].unique()
            )
            st.write(asset_data[asset_data["name"] == selected_name])
        if st.checkbox("Filter Changes"):
            asset_data = pd.read_csv("../changes.csv")
            selected_name = st.selectbox(
                "Account to filter",
                options=asset_data["changed_item"].unique()
            )
            st.write(asset_data[asset_data["changed_item"] == selected_name])