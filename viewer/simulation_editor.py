import streamlit as st
import streamlit_nested_layout

from planner import Simulation

from edit_transaction import edit_transaction

def edit_simulation(simulation: Simulation) -> Simulation:
    if st.checkbox("Edit Start"):
        simulation.start = st.date_input(
            "Simulation Start Date",
            value=simulation.start,
        )
    if st.checkbox("Edit End"):
        simulation.end = st.date_input(
            "Simulation Start Date",
            value=simulation.end,
        )
    if st.checkbox("Edit Transactions"):
        with st.expander("Edited Transactions"):
            editable_transactions = st.number_input(
                "Number of Transactions to edit",
                value = 1,
                min_value=0,
                step=1,
                max_value=len(simulation.transactions)
            )
            if editable_transactions > 0:
                transaction_names = [t.name for t in simulation.transactions]
                for transaction_order in range(editable_transactions):
                    with st.expander(f"Edited Transaction {transaction_order}"):
                        selected_transaction_name = st.selectbox(
                            f"Transaction {transaction_order} Name",
                            options=transaction_names,
                        )
                        transaction_index = transaction_names.index(selected_transaction_name)                    
                        simulation.transactions[transaction_index] = edit_transaction(
                            simulation, 
                            simulation.transactions[transaction_index],
                            label=transaction_order,
                        )
                # For any dates and assignments that were changed
                simulation.setup()
    return simulation