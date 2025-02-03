import pandas as pd
import streamlit as st
import plotly.express as px

def view_taxes(actions: pd.DataFrame):
    view_deductions(actions)

def view_deductions(actions: pd.DataFrame):
    deductions = actions.loc[actions["fed_tax_deductible"], :]
    st.markdown("Tax Deductable Actions:")
    st.write(deductions)
    deductions["year"] = deductions["date"].dt.year
    year_summary = deductions[["year", "description", "amount"]].groupby(["year", "description"]).sum().reset_index(drop=False)
    st.plotly_chart(px.bar(
        year_summary,
        x="year",
        y="amount",
        color="description",
    ))
