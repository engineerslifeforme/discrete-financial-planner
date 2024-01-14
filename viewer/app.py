import streamlit as st
import plotly.express as px
import pandas as pd

""" # Plan Results Viewer"""

data = pd.read_csv("../output.csv")
st.plotly_chart(px.line(
    data,
    x="date",
    y="balance",
    color="name",
))
data = pd.read_csv("../networth.csv")
st.plotly_chart(px.line(
    data,
    x="date",
    y="balance",
    color="type",
))
if st.checkbox("Show Expenses", value=True):
    data = pd.read_csv("../changes.csv", parse_dates=["date"])
    data = data.loc[~data["asset_maturity"], :]
    data = data.loc[data["amount"] < 0.00, :]
    account_options = data["changed_item"].unique()
    selected_accounts = st.multiselect(
        "Displayed Account Sources",
        account_options,
        default=account_options,
    )
    data["year"] = data["date"].dt.year
    data = data.loc[data["changed_item"].isin(selected_accounts), :]
    data = data.groupby(["year", "transaction_name"]).sum().reset_index(drop=False)
    st.plotly_chart(px.bar(
        data,
        x="year",
        y="amount",
        color="transaction_name",
    ))
if st.checkbox("Show Fed Taxes", value=True):
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