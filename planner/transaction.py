from decimal import Decimal
from strenum import StrEnum
from datetime import date

from pydantic import BaseModel

from planner.common import (
    ZERO, 
    DateBaseModel,
)

class InsufficientBalanceException(Exception):
    pass

class FrequencyEnum(StrEnum):
    monthly = "monthly"
    daily = "daily"
    biweekly = "biweekly"
    yearly = "yearly"
    weekly = "weekly"

class Transaction(DateBaseModel):
    amount: Decimal = ZERO
    amount_remaining_balance: bool = False
    amount_above: Decimal = None
    frequency: FrequencyEnum = FrequencyEnum.monthly
    frequency_periods: int = 1
    source: str = None
    asset_maturity: bool = False
    destination: str = None
    present_value_date: date = None
    amount_required: bool = True
    income_taxable: bool = False
    income_tax_payment: bool = False
    tax_deductable: bool = False
    period_counter: int = 0 # Private
    last_executed: date = None # Private

    def get_amount(self, current_date: date, deposit: bool) -> float:
        """ Get transaction amount at current point in time

        :param current_date: date to assess amount
        :type current_date: date
        :param deposit: whether the transaction is a deposit (true) or withdrawal (false)
        :type deposit: bool
        :return: value at requested date
        :rtype: float
        """
        return_amount = 0.0
        if self.amount_remaining_balance:
            source_remaining_balance = self.source.f_balance
            if source_remaining_balance > 0.0:
                return_amount = source_remaining_balance
        elif self.amount_above is not None:
            float_threshold = float(self.amount_above)
            if self.source.f_balance >= float_threshold:
                return_amount = self.source.f_balance - float_threshold
        elif self.asset_maturity:
            return_amount = self.interest_rate.calculate_value(
                float(self.destination.f_balance),
                self.present_value_date,
                current_date,
            ) - self.destination.f_balance
            self.present_value_date = current_date
        else:
            return_amount = self.interest_rate.calculate_value(
                float(self.amount),
                self.present_value_date,
                current_date,
            )
        if self.source is not None:
            if return_amount > self.source.f_balance:
                if self.amount_required:
                    raise(InsufficientBalanceException(f"Transaction {self.name} cannot get sufficient funds ({round(return_amount)}) on {current_date} from source {self.source.name}"))
                else:
                    return self.source.f_balance
        return return_amount

    def setup(self, start_date: date, end_date: date, asset_dict: dict, interest_rates: dict, date_dict: dict):
        """Setup defaults and linkages and check for correctness

        :param start_date: simulation start date
        :type start_date: date
        :param end_date: simulation end date
        :type end_date: date
        :param asset_dict: dictionary of assets keyed by name
        :type asset_dict: dict
        :param interest_rates: dictionary by name of interest rates
        :type interest_rates: dict
        :param date_dict: dictionary of special dates keyed by name
        :type date_dict: dict
        """
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
        # will cause transaction to happen on first valid date
        self.period_counter = self.frequency_periods
        self.get_interest_rate(interest_rates)
        self.setup_dates(start_date, end_date, date_dict)
        self.check()

    def check(self):
        """ Check the integrity of the Transaction definition
        """
        assert(self.source is not None or self.destination is not None), "Transactions must have at least a source or destination"
        if self.amount_remaining_balance:
            assert(self.source is not None), f"Transaction {self.name} cannot transfer remaining balance without a defined source"
        if self.amount_above is not None:
            assert(self.source is not None), f"Transaction {self.name} cannot transfer balance above threshold without a defined source"
        if self.asset_maturity:
            assert(self.destination is not None), f"Asset Maturity transaction ({self.name}) must have a valid destination"

    def executable(self, current_date: date) -> bool:
        """ Determine if transaction should be executed on date

        :param current_date: date of potential execution
        :type current_date: date
        :return: true = should execute, false = should not
        :rtype: bool
        """
        execute = False
        if current_date >= self.start_date and current_date <= self.end_date:
            if self.frequency == FrequencyEnum.daily:
                execute = True
            elif self.frequency == FrequencyEnum.yearly:
                if current_date.day == self.start_date.day and current_date.month == self.start_date.month:
                    execute = True
            elif self.frequency == FrequencyEnum.monthly:
                if current_date.day == self.start_date.day:
                    execute = True
            else:
                if self.last_executed is None:
                    if self.frequency in [FrequencyEnum.biweekly, FrequencyEnum.weekly]:
                        if current_date.day == self.start_date.day:
                            execute = True
                else:
                    if self.frequency == FrequencyEnum.biweekly:
                        if (current_date - self.last_executed).days == 14:
                            execute = True
                    elif self.frequency == FrequencyEnum.weekly:
                        if (current_date - self.last_executed).days == 7:
                            execute = True
                    else:
                        raise(ValueError(f"Unknown transaction frequency: {self.frequency}"))
        if execute:
            self.period_counter += 1
            if self.period_counter >= self.frequency_periods:
                self.period_counter = 0
            else:
                execute = False
        if execute:
            self.last_executed = current_date
        return execute

