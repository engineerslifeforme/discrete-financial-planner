from decimal import Decimal
from datetime import date
import math

from planner.transaction import Transaction, FrequencyEnum
from planner.common import round, ZERO, amortorize

class Mortgage(Transaction):
    loan_amount: Decimal
    loan_rate: float
    term_months: int
    extra_principal: Decimal = ZERO

    @property
    def loan_rate_month(self):
        return self.loan_rate / 100.0 / 12.0
    
    @property
    def payment_interest(self):
        return float(abs(self.destination.f_balance)) * self.loan_rate_month
    
    def check(self):
        """ Assure the mortgage is configured correctly
        """
        super().check()
        assert(self.source is not None), f"Mortgage {self.name} does not have a source defined"
        assert(self.destination is not None), f"Mortgage {self.name} does not have a destination defined"
        assert(self.frequency == FrequencyEnum.monthly), f"Mortgage must have a monthly frequency, not {self.frequency}"

    def get_amount(self, current_date: date, deposit: bool) -> float:
        """ Get transaction amount at current point in time

        :param current_date: date to assess amount
        :type current_date: date
        :param deposit: whether the transaction is a deposit (true) or withdrawal (false)
        :type deposit: bool
        :return: value at requested date
        :rtype: float
        """
        payment = amortorize(self.loan_rate_month, float(self.term_months), float(self.loan_amount))
        payment += float(self.extra_principal)
        payment_principal = payment - self.payment_interest
        # Pay against debt/mortgage
        closeout = False
        if abs(self.destination.f_balance) < payment_principal:
            closeout = True
        if deposit:
            if closeout:
                return_amount = abs(self.destination.f_balance)
            else:
                return_amount = payment_principal
        else:
            if closeout:
                return_amount = self.payment_interest + abs(self.destination.f_balance)
            else:
                return_amount = payment
        return return_amount

    def executable(self, *args, **kwargs) -> bool:
        """ Additional special logic on when to run mortgage transactions

        :return: true = should execute, false = should not
        :rtype: bool
        """
        if self.destination.get_balance() == ZERO:
            return False
        else:
            return super().executable(*args, **kwargs)