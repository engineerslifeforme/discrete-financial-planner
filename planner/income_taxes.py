from decimal import Decimal
from datetime import date

from pydantic import BaseModel
from typing import List, Dict, Tuple

from planner.transaction import Transaction
from planner.common import round, ZERO, InterestBaseModel
from planner.tax_deduction import TaxDeduction

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

class YearSummary(BaseModel):
    year: int
    taxable_income: Decimal
    deductions: Decimal
    income_post_deductions: Decimal
    taxes_owed_pre_credits: Decimal
    credits: Decimal
    taxes_prepaid: Decimal
    tax_bill: Decimal
    max_rate: float
    balance_at_max_rate: Decimal

class IncomeTaxCaculator(InterestBaseModel):
    source: str
    deductions: List[TaxDeduction] = []
    credits: List[TaxDeduction] = []
    tax_brackets: List[Dict[str, float]] = TAX_BRACKETS
    summaries: List[YearSummary] = [] # Private
    relative_year: int = None # Private

    def setup(self, asset_dict: dict, relative_year: int):
        """ Setup tax source mapping

        :param asset_dict: dictionary of names to asset objects
        :type asset_dict: dict
        :param relative_year: year from which to grow
        :type relative_year: int
        """
        try:
            self.source = asset_dict[self.source]
        except KeyError:
            raise(ValueError(f"Unknown source ({self.source}) on Federal Income Taxes"))
        self.relative_year = relative_year
        for deduction in self.deductions:
            deduction.setup(relative_year)
        for credit in self.credits:
            credit.setup(relative_year)

    def get_interest_rate(self, interest_rates: dict):
        """ Need to push down interest rate assignments to subobjects

        :param interest_rates: dictionary of interest rates keyed by name
        :type interest_rates: dict
        """
        super().get_interest_rate(interest_rates)
        for deduction in self.deductions:
            deduction.get_interest_rate(interest_rates)
        for credit in self.credits:
            credit.get_interest_rate(interest_rates)

    def build_full_bracket_amounts(self, taxed_amounts: list) -> list:
        """Build list of tax cost per full bracket

        :param taxed_amounts: ordered list of tax amounts with rate
        :type taxed_amounts: list
        :return: list of the full cost of each bracket
        :rtype: list
        """
        full_amounts = []
        for bracket_size, bracket_rate in taxed_amounts:
            full_amounts.append(bracket_size * bracket_rate)
        return full_amounts
    
    def build_rates_list(self, year: int) -> list:
        """ Build incremental quantity of money with rate
        
        :param year: current year of taxes
        :type year: int
        :return: list of bracket income size and rate
        :rtype: list
        """
        taxed_amounts = []
        brackets = [
            (self.interest_rate.calculate_value(
                b["bottom_of_range"],
                date(self.relative_year, 1, 1),
                date(year, 1, 1),
            ), b["rate"])
            for b in self.tax_brackets
        ]
        for index, bracket in enumerate(brackets):
            try:
                taxed_amounts.append((brackets[index+1][0] - bracket[0], bracket[1]))
            except IndexError:
                taxed_amounts.append((100000000000.0, bracket[1]))
        return taxed_amounts

    def calculate_taxes(self, action_logs: list, year: int, federal: bool, mortgage_interest: float) -> Transaction:        
        """Calculate taxes owed on income

        :param action_logs: transactions for the year
        :type action_logs: list
        :param year: year of taxes and actions
        :type year: int
        :param federal: is federal taxes, True = Yes, False = State
        :type federal: bool
        :return: a transaction for taxes owed (or refunded)
        :rtype: Transaction
        """
        taxable_income = sum([a.amount for a in action_logs if a.transaction.income_taxable and a.amount > ZERO])
        balance = float(taxable_income)
        if federal:
            deductions = sum([a.amount for a in action_logs if a.transaction.fed_tax_deductable])
        else: # state
            deductions = sum([a.amount for a in action_logs if a.transaction.state_tax_deductable])
        deductions -= round(Decimal(sum([d.get_amount(year) for d in self.deductions if d.executable(year)])))
        # This is technically not good, losing some precision I htink
        deductions -= round(Decimal(mortgage_interest))
        balance += float(deductions)
        income_post_deductions = round(Decimal(balance))
        taxed_amounts = self.build_rates_list(year)
        full_amounts = self.build_full_bracket_amounts(taxed_amounts)
        taxes_owed = 0.0
        bracket_index = 0        
        while balance > 0.0:
            # Use later to capture how much money was in the highest bracket
            entering_balance = balance
            bracket_quantity, bracket_rate = taxed_amounts[bracket_index]
            if balance > bracket_quantity:
                taxes_owed += full_amounts[bracket_index]
                balance -= bracket_quantity
            else:
                taxes_owed += balance * bracket_rate
                balance -= balance
            bracket_index += 1
        taxes_owed_pre_credits = round(Decimal(taxes_owed))
        # Tax payment actions have a negative amount
        # so they are added to decrease taxes owed
        if federal:
            taxes_paid = sum([a.amount for a in action_logs if a.transaction.fed_income_tax_payment])
        else: # state
            taxes_paid = sum([a.amount for a in action_logs if a.transaction.state_income_tax_payment])
        taxes_owed += float(taxes_paid)
        credit_total = sum([c.get_amount(year) for c in self.credits if c.executable(year)])
        taxes_owed -= credit_total
        
        self.summaries.append(YearSummary(
            year = year,
            taxable_income = taxable_income,
            deductions = deductions,
            income_post_deductions = income_post_deductions,
            taxes_owed_pre_credits = taxes_owed_pre_credits,
            credits = round(Decimal(credit_total)),
            taxes_prepaid = taxes_paid,
            tax_bill = round(Decimal(taxes_owed)),
            max_rate = taxed_amounts[bracket_index-1][1],
            balance_at_max_rate=round(Decimal(entering_balance)),
        ))
        
        deposit = False
        if taxes_owed < 0.0:
            deposit = True
            taxes_owed = abs(taxes_owed)
        if federal:
            tax_str = "Federal"
        else:
            tax_str = "State"
        return_transaction = Transaction(
            name=f"{year} {tax_str} Income Taxes",
            amount=round(Decimal(taxes_owed)),
            source=self.source.name,
        )
        # Pydantic won't allow direct assignment
        # the way the delayed assignment is handled
        return_transaction.source = self.source
        return return_transaction, deposit
    
    def summarize(self) -> list:
        """ Summarize tax history

        :return: list of dictionaries of yearly data
        :rtype: list
        """
        return [s.dict() for s in self.summaries]