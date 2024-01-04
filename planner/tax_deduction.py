from decimal import Decimal
from datetime import date

from planner.common import NamedInterestBaseModel, ZERO

class TaxDeduction(NamedInterestBaseModel):
    amount: Decimal = ZERO
    start_year: int = None
    end_year: int = None
    relative_year: int = None # Private

    def setup(self, year: int):
        """ Initialize data

        :param year: _description_
        :type year: int
        """
        self.relative_year = year

    def executable(self, year: int) -> bool:
        """ Is Deduction valid in this year

        :param year: year in which to check validity
        :type year: int
        :return: True = valid, False = not valid
        :rtype: bool
        """
        if self.end_year is None and self.start_year is None:
            return True
        elif self.end_year is None:
            return year >= self.start_year
        elif self.start_year is None:
            return year <= self.end_year
        else:
            return year >= self.start_year and year <= self.end_year
    
    def get_amount(self, year: int) -> float:
        """ Determine amount to deduct

        :param year: year in which to calculate
        :type year: int
        :return: amount to be deducted
        :rtype: float
        """
        return self.interest_rate.calculate_value(
            float(self.amount),
            date(self.relative_year, 1, 1),
            date(year, 1, 1),
        )
