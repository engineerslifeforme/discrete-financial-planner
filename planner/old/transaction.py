from decimal import Decimal
from strenum import StrEnum
from datetime import date
from typing import List, Union, Dict, Any

from pydantic import BaseModel

from planner.common import (
    ZERO, 
    DateBaseModel,
    InsufficientBalanceException,
    amortorize,
)
from planner.life_expectancy import LIFE_EXPECTANCY

sepp_payments = {}

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
    maintain_balance: Decimal = None
    frequency: FrequencyEnum = FrequencyEnum.monthly
    frequency_periods: int = 1
    source: str = None
    asset_maturity: bool = False
    destination: str = None
    present_value_date: date = None
    amount_required: bool = True
    income_taxable: bool = False
    fed_income_tax_payment: bool = False
    state_income_tax_payment: bool = False
    fed_tax_deductable: bool = False
    state_tax_deductable: bool = False
    category: str = None
    priority: int = 100
    contributions_only: bool = False
    sepp_birth: date = None
    sepp_interest_rate_yearly: float = None
    min_withdrawal_date_exception: bool = False
    donation_factor: float = None
    donation_source: str = None
    donation_name: str = ""
    donation_transaction: "Transaction" = None # Private
    period_counter: int = 0 # Private
    last_executed: date = None # Private
    raw_data: Dict[str, Any] = None    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.raw_data = kwargs

    def get_amount(self, current_date: date, deposit: bool, is_donation: bool = False) -> float:
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
        elif self.sepp_birth is not None and self.sepp_interest_rate_yearly is not None:
            try:
                return_amount = sepp_payments[self.name]
            except KeyError:
                # hasn't been calculated yet
                age = int((current_date - self.sepp_birth).days / 365.0)
                age_factor = LIFE_EXPECTANCY[age]
                return_amount = amortorize(
                    self.sepp_interest_rate_yearly / 100.0,
                    age_factor,
                    self.source.f_balance
                )
                sepp_payments[self.name] = return_amount
        elif self.sepp_birth is not None:
            age = int((current_date - self.sepp_birth).days / 365.0)
            age_factor = LIFE_EXPECTANCY[age]
            return_amount = self.source.f_balance / age_factor
        elif self.amount_above is not None:
            float_threshold = float(self.amount_above)
            if self.source.f_balance >= float_threshold:
                return_amount = self.source.f_balance - float_threshold
        elif self.maintain_balance is not None:
            deposit_needed = float(self.maintain_balance) - self.destination.f_balance
            if deposit_needed > 0.0:
                return_amount = deposit_needed
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
                    return_amount = self.source.f_balance
            if self.contributions_only:
                if return_amount > self.source.contribution_balance:
                    if self.amount_required:
                        raise(InsufficientBalanceException(f"Transaction {self.name} cannot get sufficient contribution funds ({round(return_amount)}) on {current_date} from source {self.source.name}, contribution balance {self.source.contribution_balance}"))
                    else:
                        return_amount = self.source.contribution_balance
        if is_donation:
            return_amount *= self.donation_factor
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
            except TypeError:
                # has already been assigned so using as dict key will fail
                pass
        if self.destination is not None:
            try:
                self.destination = asset_dict[self.destination]
            except KeyError:
                raise(ValueError(f"Unknown destination ({self.destination}) on transaction {self.name}"))        
            except TypeError:
                # has already been assigned so using as dict key will fail
                pass
        if self.donation_source is not None:
            try:
                self.donation_source = asset_dict[self.donation_source]
            except KeyError:
                raise(ValueError(f"Unknown donation source ({self.donation_source}) on transaction {self.name}"))        
            except TypeError:
                # has already been assigned so using as dict key will fail
                pass
        # will cause transaction to happen on first valid date
        self.period_counter = self.frequency_periods
        self.get_interest_rate(interest_rates)
        self.setup_dates(start_date, end_date, date_dict)
        self.check()
        if self.category is None:
            self.category = f"{self.name} (Uncategorized)"

    def check(self):
        """ Check the integrity of the Transaction definition
        """
        assert(self.source is not None or self.destination is not None), f"Transaction {self.name} must have at least a source or destination"
        if self.amount_remaining_balance:
            assert(self.source is not None), f"Transaction {self.name} cannot transfer remaining balance without a defined source"
        if self.amount_above is not None:
            assert(self.source is not None), f"Transaction {self.name} cannot transfer balance above threshold without a defined source"
        if self.asset_maturity:
            assert(self.destination is not None), f"Asset Maturity transaction ({self.name}) must have a valid destination"
        if self.contributions_only:
            assert(self.source is not None), f"Source not defined on {self.name}, required for contribution withdrawal limiting"
        assert(not (self.fed_income_tax_payment and self.state_income_tax_payment)), f"Transaction {self.name} cannot be both a payment for state AND federal income taxes"
        if self.fed_income_tax_payment or self.state_income_tax_payment:
            assert(self.destination is None), f"Transaction {self.name} is a tax payment and therefore cannot have a destiation"
        if self.sepp_birth is not None:
            assert(self.source is not None), f"Transaction {self.name} must have a source for a SEPP transaction"
            assert(self.destination is not None), f"Transaction {self.name} must have a destination for a SEPP transaction"
            assert(self.frequency == FrequencyEnum.yearly), f"Transaction {self.name} must be yearly frequency for SEPP payments"
        if self.sepp_interest_rate_yearly is not None:
            assert(self.sepp_birth is not None), f"Transaction {self.name} a sepp_birth is required for SEPP payments as a reference for life expectancy"
        if self.donation_factor is not None:
            assert(self.donation_source is not None), f"Transaction {self.name} has a donation factor but no donation source"

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
    
    def to_dict(self) -> dict:
        """ Capturing static data

        :return: dictionary of some static data
        :rtype: dict
        """
        return {
            "transaction_name": self.name,
            "asset_maturity": self.asset_maturity,
            "income_taxable": self.income_taxable,
            "fed_income_tax_payment": self.fed_income_tax_payment,
            "state_income_tax_payment": self.state_income_tax_payment,
            "fed_tax_deductable": self.fed_tax_deductable,
            "state_tax_deductable": self.state_tax_deductable,
            "category": self.category,
            "sepp": self.sepp_birth is not None,
        }

class TransactionGroup(Transaction):
    sub_transactions: List[Union["TransactionGroup", Transaction]]

    def to_transaction_list(self, parent_base: dict = None) -> list:
        if parent_base is None:
            parent_base = {}
        parent_copy = parent_base.copy()
        parent_copy.update(self.raw_data)
        del parent_copy["sub_transactions"]
        transaction_list = []        
        for sub in self.sub_transactions:
            base_copy = parent_copy.copy()
            try:
                transaction_list.extend(sub.to_transaction_list(parent_base=base_copy))
            except AttributeError:                
                base_copy.update(sub.raw_data)
                transaction_list.append(Transaction(**base_copy))
        return transaction_list
    
    def check(self):
        raise NotImplemented()
