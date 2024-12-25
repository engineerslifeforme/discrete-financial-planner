from datetime import date

from pydantic import BaseModel

from planner.common import future_value

class InterestRate(BaseModel):
    name: str
    rate: float = 0.0 # Yearly % rate

    @property
    def daily_rate(self) -> float:
        """Interest rate in decimal per day

        :return: decimal rate per day
        :rtype: float
        """
        return (self.rate / 100.0) / 365.0
    
    def calculate_value(self, present_value: float, present_date: date, future_date: date) -> float:
        """ Calculate future value using this interest rate

        :param present_value: present value
        :type present_value: float
        :param present_date: date of present value
        :type present_date: date
        :param future_date: request date of future value
        :type future_date: date
        :return: future value at requested date
        :rtype: float
        """
        if self.rate == 0.0:
            return present_value
        else:
            return future_value(
                present_value, 
                self.daily_rate, 
                (future_date - present_date).days,
            )