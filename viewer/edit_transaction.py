from decimal import Decimal

import streamlit as st

from planner.transaction import Transaction
from planner import Simulation

def edit_transaction(simulation: Simulation, transaction: Transaction, label: str = "") -> Transaction:
    if st.checkbox(f"Show Details for Transaction {label}"):
        st.write(transaction)
    if st.checkbox(f"Change Amount for Transaction {label}"):
        transaction.amount = Decimal(st.number_input(
            f"New Amount for Transaction {label}",
            value=float(transaction.amount),
            min_value=0.00,
            step=0.01,
        ))
    if st.checkbox(f"Change Start Date for Transaction {label}"):
        date_types = ["Named", "Specific"]
        date_type = st.radio(
            f"Date Input Type for Transaction {label}",
            options=date_types
        )
        named_date = date_type == date_types[0]
        if named_date:
            date_names = list(simulation.dates.keys())
            date_labels = {
                f"{name} ({date})": name for name, date in simulation.dates.items()
            }
            if transaction.start is None:
                default_index = 0
            else:
                default_index = date_names.index(transaction.start)
            transaction.start = date_labels[st.selectbox(
                f"New Named Date for Transaction {label}",
                options=list(date_labels.keys()),
                index=default_index,
            )]
        else:
            transaction.start = None
            transaction.start_date = st.date_input(
                f"New Start Date for Transaction {label}",
                value=transaction.start_date
            )
    return transaction