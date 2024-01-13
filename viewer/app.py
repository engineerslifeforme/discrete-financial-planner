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