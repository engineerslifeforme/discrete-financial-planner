from decimal import Decimal
from datetime import date

from pydantic import BaseModel

from planner.common import ZERO, round, DEFAULT_INTEREST, InterestBaseModel
from planner.interest_rate import InterestRate
from planner.transaction import Transaction

class Asset(InterestBaseModel):
    balance: Decimal = ZERO
    f_balance: float = 0.0

    def __init__(self, *args, **kwargs):
        """ Asset initialization

        Because the running balance is tracked as a float
        it is necessary to create it at initialization requiring
        this custom initaliazation
        """
        super().__init__(*args, **kwargs)
        self.f_balance = float(kwargs.get("balance", ZERO))

    def mature(self) -> tuple:
        """Mature 1 day

        :return: tuple of new balance and balance change
        :rtype: tuple
        """
        change = self.interest_rate.daily_rate * self.f_balance
        self.f_balance += change
        return self.f_balance, change
    
    @property
    def balance(self) -> Decimal:
        """ Provide the running balance as Decimal

        :return: running balance as Decimal
        :rtype: Decimal

        The running balance is really tracked as a float
        but this allows a friendly value to be provided
        """
        return round(Decimal(self.f_balance))
    
    def get_state(self, date: date) -> dict:
        """ Get representation of state for logging

        :param date: date of state
        :type date: date
        :return: dictionary representation of state
        :rtype: dict
        """
        return {
            "date": date,
            "name": self.name,
            "balance": str(self.balance)
        }
    
    def execute_transaction(self, transaction: Transaction, deposit: bool, current_date: date) -> Decimal:
        """ Execute transaction on asset balance

        :param transaction: transaction to be executed
        :type transaction: Transaction
        :param deposit: whether the transaction is a deposit (true) or withdrawal (false)
        :type deposit: bool
        :param current_date: date of transaction
        :type current_date: date
        :return: new balance of asset post transaction
        :rtype: Decimal
        """
        if deposit:
            self.f_balance += transaction.get_amount(current_date)
        else:
            self.f_balance -= transaction.get_amount(current_date)
        return self.balance
