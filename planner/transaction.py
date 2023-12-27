from decimal import Decimal
from strenum import StrEnum
from datetime import date

from pydantic import BaseModel

from planner.common import ZERO, DEFAULT_INTEREST, InterestBaseModel

class FrequencyEnum(StrEnum):
    monthly = "monthly"
    daily = "daily"
    biweekly = "biweekly"

class Transaction(InterestBaseModel):
    amount: Decimal = ZERO
    frequency: FrequencyEnum = FrequencyEnum.monthly
    start: date = None
    end: date = None
    source: str = None
    destination: str = None
    present_value_date: date = None
    last_executed: date = None # Private

    def get_amount(self, current_date: date) -> float:
        """ Get transaction amount at current point in time

        :param current_date: date to assess amount
        :type current_date: date
        :return: value at requested date
        :rtype: float
        """
        return self.interest_rate.calculate_value(
            float(self.amount),
            self.present_value_date,
            current_date,
        )

    def setup(self, start_date: date, end_date: date, asset_dict: dict, interest_rates: dict):
        """Setup defaults and linkages and check for correctness

        :param start_date: simulation start date
        :type start_date: date
        :param end_date: simulation end date
        :type end_date: date
        :param asset_dict: dictionary of assets keyed by name
        :type asset_dict: dict
        :param interest_rates: dictionary by name of interest rates
        :type interest_rates: dict
        """
        if self.start is None:
            self.start = start_date
        if self.end is None:
            self.end = end_date
        if self.present_value_date is None:
            self.present_value_date = start_date
        if self.source is not None:
            try:
                self.source = asset_dict[self.source]
            except KeyError:
                raise(ValueError(f"Unknown source ({self.source}) on transaction {self.name}"))
        if self.destination is not None:
            try:
                self.destination = asset_dict[self.destination]
            except KeyError:
                raise(ValueError(f"Unknown destination ({self.destination}) on transaction {self.name}"))        
        self.get_interest_rate(interest_rates)
        self.check()

    def check(self):
        """ Check the integrity of the Transaction definition
        """
        assert(self.source is not None or self.destination is not None), "Transactions must have at least a source or destination"

    def executable(self, current_date: date) -> bool:
        """ Determine if transaction should be executed on date

        :param current_date: date of potential execution
        :type current_date: date
        :return: true = should execute, false = should not
        :rtype: bool
        """
        execute = False
        if current_date >= self.start and current_date <= self.end:
            if self.last_executed is None:
                if self.frequency == FrequencyEnum.daily:
                    execute = True
                elif self.frequency in [FrequencyEnum.monthly, FrequencyEnum.biweekly]:
                    if current_date.day == self.start.day:
                        execute = True
            else:
                if self.frequency == FrequencyEnum.daily:
                    if current_date != self.last_executed:
                        execute = True
                elif self.frequency == FrequencyEnum.monthly:
                    if (current_date.month != self.last_executed.month or \
                        current_date.year != self.last_executed.year) and \
                        current_date.day == self.last_executed.day:
                        execute = True
                elif self.frequency == FrequencyEnum.biweekly:
                    if (current_date - self.last_executed).days == 14:
                        execute = True
                else:
                    raise(ValueError(f"Unknown transaction frequency: {self.frequency}"))
        if execute:
            self.last_executed = current_date
        return execute

