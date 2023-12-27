from decimal import Decimal
import math
from datetime import date

from pydantic import BaseModel

ZERO = Decimal("0.00")

DEFAULT_INTEREST = "Default_Interest"

class FinanceBaseModel(BaseModel):
    name: str

class InterestBaseModel(FinanceBaseModel):
    interest_rate: str = DEFAULT_INTEREST

    def get_interest_rate(self, interest_rates: dict):
        """ Link asset to real interest rate object

        :param interest_rates: dictionary by name of interest rates
        :type interest_rates: dict
        """
        try:
            self.interest_rate = interest_rates[self.interest_rate]
        except KeyError:
            raise(ValueError(f"Appreciation rate for asset {self.name}: {self.interest_rate} does not exist!"))

def round(value: Decimal) -> Decimal:
    """ Round Decimal values to 2 decimal places

    :param value: decimal value to be rounded
    :type value: Decimal
    :return: Rounded decimal value
    :rtype: Decimal
    """
    return value.quantize(ZERO)

def future_value(present_value: float, interest: float, periods: int) -> float:
    """ Future value calculation

    :param present_value: present day value
    :type present_value: float
    :param interest: rate per period
    :type interest: float
    :param periods: number of periods
    :type periods: int
    :return: future value
    :rtype: float

    https://www.realized1031.com/glossary/future-value-fv#:~:text=In%20its%20most%20basic%20form,the%20number%20of%20time%20periods.
    """
    return present_value*math.pow((1+interest), periods)

def create_value_change_log(action_type: str, action_name: str, amount: Decimal, changed_item: str, action_date: date = None) -> dict:
    return {
        "date": action_date,
        "action_type": action_type,
        "action_name": action_name,
        "amount": amount,
        "changed_item": changed_item,
    }