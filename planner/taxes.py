from dataclasses import dataclass, fields as dc_fields, asdict
from decimal import Decimal
from typing import Optional, List, Union
from datetime import date
from copy import deepcopy
import csv

from pydantic import BaseModel, field_serializer

from planner.period import PeriodModel, PeriodModelInput
from planner.action import Action
from planner.transactions import TransactionInput
from planner.util import ZERO, ONE_DAY
from planner.interest_rates import BasicInterestRate

# The top tax rate remains 37% in 2024.
# 10%: Taxable income up to $11,600.
# 12%: Taxable income over $11,600.
# 22%: Taxable income over $47,150.
# 24%: Taxable income over $100,525.
# 32%: Taxable income over $191,950.
# 35%: Taxable income over $243,725.
# 37%: Taxable income over $609,350.

TAX_BRACKETS = [
    {"bottom_of_range": 0.0, "rate": 0.10},
    {"bottom_of_range": 11600.0, "rate": 0.12},
    {"bottom_of_range": 47150.0, "rate": 0.22},
    {"bottom_of_range": 100525.0, "rate": 0.24},
    {"bottom_of_range": 191950.0, "rate": 0.32},
    {"bottom_of_range": 243725.0, "rate": 0.35},
    {"bottom_of_range": 609350.0, "rate": 0.37},
]

def record_bracket(bracket) -> dict:
    result = {}
    for index, entry in enumerate(bracket):
        for key, value in entry.items():
            result[f"{key}_{index}"] = value
    return result

@dataclass
class TaxAdjustment(PeriodModel):
    name: str
    amount: Decimal

    # TODO: Next to inflate these probably

    def is_valid(self, current_date: date) -> bool:
        return self._is_time_valid(current_date)

class TaxAdjustmentInput(PeriodModelInput):
    name: str
    amount: Decimal

    def to_dc_model(self):
        data = self.model_dump()
        return TaxAdjustment(**data)
    
    @field_serializer('amount')
    def serialize_amount(self, amount: Decimal):
        return float(amount)

@dataclass
class FederalTax:
    credits: List[TaxAdjustment]
    deductions: List[TaxAdjustment]
    payment_source: str
    payment_priority: int
    payment_date: date
    interest_rate: Union[BasicInterestRate, str]

    def __post_init__(self):
        self._first_date = None
        self._last_date = None
        self._taxable_income = 0.0
        self._fed_tax_payments = 0.0
        self._fed_tax_deductions = 0.0
        self._taxes_owed = 0.0
        self._taxes_owed_year = None
        self.transaction = TransactionInput(
            name="Temp",
            base_amount=ZERO,
            source=self.payment_source,
            destination=self.payment_source,
            priority=self.payment_priority,
            category="Federal Taxes",
        ).to_dc_model()
        self._tax_log_file = open("tax_log.csv", "w")
        fields = [
            "year",
            "taxes_owed",
            "static_deductions",
            "dynamic_deductions",
            "credits",
            "taxes_prepaid",
            "extrapolated",
            "taxable_income",
            "highest_bracket_rate",
            "amount_taxed_at_highest_bracket",
            "tax_bill",
        ]
        fields.extend(list(record_bracket(TAX_BRACKETS).keys()))
        self._tax_log = csv.DictWriter(
            self._tax_log_file, 
            fieldnames=fields,
        )
        self._tax_log.writeheader()

    def close(self):
        self._tax_log_file.close()
    
    def is_tax_day(self, current_date: date):
        return current_date.month == self.payment_date.month and current_date.day == self.payment_date.day

    def get_taxes_transaction(self):
        this_transaction = deepcopy(self.transaction)
        this_transaction.name = f"Tax Payment {self._taxes_owed_year}"
        if self._taxes_owed > 0.0:
            this_transaction.destination = None
            this_transaction.set_base_amount(Decimal(self._taxes_owed))
        elif self._taxes_owed < 0.0:
            this_transaction.source = None
            this_transaction.set_base_amount(Decimal(abs(self._taxes_owed)))
        else:
            return None
        self._taxes_owed = 0.0
        return this_transaction

    def process_action(self, action: Action, current_date: date):
        if self._last_date is None:
            self._last_date = current_date
            self._first_date = current_date
        if current_date.year != self._last_date.year:
            self._taxes_owed = self.calculate_taxes(
                self._taxable_income, 
                self._fed_tax_payments,
                self._fed_tax_deductions,
                current_date - ONE_DAY,
            )
            self._taxes_owed_year = self._last_date.year
            self._taxable_income = 0.0
            self._fed_tax_payments = 0.0
            self._fed_tax_deductions = 0.0
            self._last_date = current_date
        if action.fed_taxable and action.amount > 0.0:
            self._taxable_income += action.amount
        if action.fed_tax_payment:
            self._fed_tax_payments += action.amount
        if action.fed_tax_deductible and action.amount < 0.0:
            self._fed_tax_deductions += action.amount

    def get_tax_brackets(self, current_date: date) -> list:
        bracket = deepcopy(TAX_BRACKETS)
        days_to_inflate = (current_date.year - self._first_date.year) * 365
        for entry in bracket:
            value = entry["bottom_of_range"]
            entry["bottom_of_range"] = self.interest_rate.inflate(value, start_date=current_date, days=days_to_inflate)
        return bracket

    def calculate_taxes(self, taxable_income: float, taxes_paid: float, dynamic_deductions: float, current_date: date) -> float:
        # TODO: Extrapolate tax brackets
        # Account for leap year
        if current_date.year % 4 == 0:
            total_days = 366
        else:
            total_days = 365
        accounted_for_days = (current_date - self._last_date).days + 1
        extrapolate_partial_year = accounted_for_days != total_days
        if extrapolate_partial_year:
            factor = total_days/accounted_for_days
            dynamic_deductions = dynamic_deductions * factor
            taxable_income = taxable_income * factor
            taxes_paid = taxes_paid * factor
        balance = taxable_income
        balance += dynamic_deductions
        static_deductions = float(sum([d.amount for d in self.deductions if d.is_valid(current_date)]))
        balance -= static_deductions
        
        tax_bill = 0.0
        bracket_index = 0
        rate = 0.0
        bracket_range = 0.0
        tax_brackets = self.get_tax_brackets(current_date)
        while balance > 0.0:
            rate = tax_brackets[bracket_index]["rate"]
            bottom_limit = tax_brackets[bracket_index]["bottom_of_range"]
            try:
                top_limit = tax_brackets[bracket_index+1]["bottom_of_range"]
                bracket_range = top_limit - bottom_limit
            except IndexError:
                bracket_range = balance
            if bracket_range > balance:
                bracket_range = balance
            tax_bill += bracket_range * rate
            balance -= bracket_range
            bracket_index += 1
        total_credits = float(sum([c.amount for c in self.credits if c.is_valid(current_date)]))
        tax_bill -= total_credits
        taxes_owed = tax_bill + taxes_paid
        log = {
            "year": current_date.year,
            "taxable_income": taxable_income,
            "tax_bill": tax_bill,
            "taxes_owed": taxes_owed,
            "static_deductions": static_deductions,
            "dynamic_deductions": dynamic_deductions,
            "credits": total_credits,
            "taxes_prepaid": taxes_paid,
            "extrapolated": extrapolate_partial_year,
            "highest_bracket_rate": rate,
            "amount_taxed_at_highest_bracket": bracket_range,
        }
        log.update(record_bracket(tax_brackets))
        self._tax_log.writerow(log)
        return taxes_owed
    
    def load_interest_rate(self, interest_rates: dict):
        if self.interest_rate is not None:
            self.interest_rate = interest_rates[self.interest_rate]
            assert(type(self.interest_rate) == BasicInterestRate), "Only Basic Interest Rates supported on taxes for now"

class FederalTaxInput(BaseModel):
    payment_source: str
    credits: List[TaxAdjustmentInput] = []
    deductions: List[TaxAdjustmentInput] = []
    payment_priority: int = 80
    payment_date: date = date(2024, 4, 1)
    interest_rate: Optional[str] = None

    def to_dc_model(self):
        data = self.model_dump()
        data.pop("credits", None)
        data.pop("deductions", None)
        return FederalTax(
            credits = [t.to_dc_model() for t in self.credits],
            deductions = [t.to_dc_model() for t in self.deductions],
            **data,
        )