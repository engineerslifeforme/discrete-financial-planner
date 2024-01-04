from decimal import Decimal
import math
from datetime import date

from pydantic import BaseModel

ZERO = Decimal("0.00")

DEFAULT_INTEREST = "Default_Interest"

class InsufficientBalanceException(Exception):
    pass

class FinanceBaseModel(BaseModel):
    name: str

class InterestBaseModel(BaseModel):
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

class NamedInterestBaseModel(FinanceBaseModel, InterestBaseModel):
    pass
        
class DateBaseModel(NamedInterestBaseModel):
    start_date: date = None
    end_date: date = None
    start: str = None
    end: str = None

    def setup_dates(self, start_date: date, end_date: date, date_dict: dict):
        """ Setup date on object based on the multiple input types

        :param start_date: simulation start date
        :type start_date: date
        :param end_date: simulation end date
        :type end_date: date
        :param date_dict: dictionary of special dates keyed by name
        :type date_dict: dict

        named start takes priority of start_date in inputs
        Same for end
        No dates will default to simulation start/end
        """
        if self.start is not None:
            self.start_date = date_dict[self.start]
        if self.end is not None:
            self.end_date = date_dict[self.end]
        if self.start_date is None:
            self.start_date = start_date
        if self.end_date is None:
            self.end_date = end_date


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

