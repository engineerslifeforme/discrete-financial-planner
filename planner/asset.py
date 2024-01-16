from decimal import Decimal
from datetime import date

from pydantic import BaseModel

from planner.common import (
    ZERO, 
    round, 
    InsufficientBalanceException,
)
from planner.transaction import Transaction
from planner.action_log import ActionLog

class PrematureWithdrawalException(Exception):
    pass

class Asset(BaseModel):
    name: str
    balance: Decimal = ZERO
    f_balance: float = 0.0
    allow_negative_balance: bool = False
    min_withdrawal_date: date = None
    category: str = None

    def __init__(self, *args, **kwargs):
        """ Asset initialization

        Because the running balance is tracked as a float
        it is necessary to create it at initialization requiring
        this custom initaliazation
        """
        super().__init__(*args, **kwargs)
        self.f_balance = float(kwargs.get("balance", ZERO))
        if self.category is None:
            self.category = self.name

    def get_balance(self) -> Decimal:
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
            "balance": str(self.get_balance()),
            "category": self.category,
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
            if self.min_withdrawal_date is not None:
                if current_date < self.min_withdrawal_date:
                    raise(PrematureWithdrawalException(f"Withdrawals not allowed for {self.name} prior to {self.min_withdrawal_date}, attempted on {current_date}"))
            amount = -1.0 * transaction.get_amount(current_date, deposit)
        self.f_balance += amount
        if not self.allow_negative_balance:
            if self.f_balance < 0.0:
                raise(InsufficientBalanceException(f"Asset {self.name} is not allowed to have a negative balance, caused by transaction {transaction.name} on {current_date}"))
        log = ActionLog(
            action_type="Asset Transaction",
            transaction=transaction,
            amount=round(Decimal(amount)),
            changed_item=self.name,
            date = current_date,
        )
        return self.get_balance(), amount, log
