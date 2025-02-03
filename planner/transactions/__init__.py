from typing import Union

from planner.transactions.transaction import Transaction, TransactionInput
from planner.transactions.sweep import Sweep, SweepInput
from planner.transactions.mortgage import Mortgage, MortgageInput
from planner.transactions.maturation import Maturation, MaturationInput
from planner.transactions.maintain import MaintainBalance, MaintainBalanceInput
from planner.transactions.sepp import Sepp, SeppInput

transaction_options = Union[Mortgage, MaintainBalance, Maturation, Sweep, Sepp, Transaction]
transaction_input_options = Union[MortgageInput, MaintainBalanceInput, MaturationInput, SweepInput, SeppInput, TransactionInput]