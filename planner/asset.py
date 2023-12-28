from decimal import Decimal
from datetime import date

from pydantic import BaseModel

from planner.common import (
    ZERO, 
    round, 
    InterestBaseModel,
    create_value_change_log,
)
from planner.transaction import Transaction

class Asset(InterestBaseModel):
    balance: Decimal = ZERO
    f_balance: float = 0.0
    allow_negative_balance: bool = False

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

        :return: tuple of new balance, balance change, change log
        :rtype: tuple
        """
        change = self.interest_rate.daily_rate * self.f_balance
        self.f_balance += change
        log = create_value_change_log(
            "Asset Maturity",
            "1 Day",
            round(Decimal(change)),
            changed_item= self.name,
        )
        return self.f_balance, change, log
    
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
    
    def execute_transaction(self, transaction: Transaction, deposit: bool, current_date: date) -> tuple:
        """ Execute transaction on asset balance

        :param transaction: transaction to be executed
        :type transaction: Transaction
        :param deposit: whether the transaction is a deposit (true) or withdrawal (false)
        :type deposit: bool
        :param current_date: date of transaction
        :type current_date: date
        :return: new balance of asset post transaction and log
        :rtype: tuple
        """
        if deposit:
            amount = transaction.get_amount(current_date, deposit)
        else:
            amount = -1.0 * transaction.get_amount(current_date, deposit)
        self.f_balance += amount
        if not self.allow_negative_balance:
            assert(self.f_balance >= 0.0), f"Asset {self.name} is not allowed to have a negative balance, caused by transaction {transaction.name} on {current_date}"
        log = create_value_change_log(
            "Asset Transaction",
            transaction.name,
            round(Decimal(amount)),
            self.name,
            action_date = current_date,
        )
        return self.balance, log
