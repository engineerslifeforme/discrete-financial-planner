from decimal import Decimal

from pydantic import BaseModel
from typing import List, Dict, Tuple

from planner.transaction import Transaction
from planner.common import round
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

class FederalIncomeTaxCaculator(BaseModel):
    source: str
    deductions: List[TaxDeduction] = []
    credits: List[TaxDeduction] = []
    tax_brackets: List[Dict[str, float]] = TAX_BRACKETS
    yearly_taxable_income: Dict[int, float] = {} # Private
    yearly_taxes_prepaid: Dict[int, float] = {} # Private
    yearly_taxes_owed: Dict[int, float] = {} # Private
    yearly_tax_bill: Dict[int, float] = {} # Private
    taxed_amounts: List[Tuple[float, float]] = [] # Private
    full_amounts: List[float] = [] # Private
    yearly_deductions: Dict[int, float] = {} # Private
    yearly_credits: Dict[int, float] = {} # Private

    def new_year(self, year: int):
        """Initializes a new year tracking

        :param year: year as integer
        :type year: int

        Only for those incremented over time
        """
        self.yearly_taxable_income[year] = 0.0
        self.yearly_taxes_prepaid[year] = 0.0
        self.yearly_deductions[year] = 0.0
        self.yearly_credits[year] = 0.0

    def update_taxable_income(self, year: int, amount: float):
        """ Track taxable income

        :param year: year of income
        :type year: int
        :param amount: amount increment of income
        :type amount: float
        """
        self.yearly_taxable_income[year] += amount

    def update_taxes_paid(self, year: int, amount: float):
        """ UPdate taxes paid

        :param year: year of tax payment
        :type year: int
        :param amount: amount of taxes paid
        :type amount: float
        """
        self.yearly_taxes_prepaid[year] += amount

    def update_deductions(self, year: int, amount: float):
        """ Update year deductions total

        :param year: year of deduction
        :type year: int
        :param amount: amount of deduction
        :type amount: float
        """
        self.yearly_deductions[year] += amount

    def setup(self, asset_dict: dict):
        """ Setup tax source mapping

        :param asset_dict: dictionary of names to asset objects
        :type asset_dict: dict
        """
        self.taxed_amounts = self.build_rates_list()
        self.full_amounts = self.build_full_bracket_amounts()
        try:
            self.source = asset_dict[self.source]
        except KeyError:
            raise(ValueError(f"Unknown source ({self.source}) on Federal Income Taxes"))

    def build_full_bracket_amounts(self) -> list:
        """ Build list of tax cost per full bracket

        :return: list of the full cost of each bracket
        :rtype: list
        """
        full_amounts = []
        for bracket_size, bracket_rate in self.taxed_amounts:
            full_amounts.append(bracket_size * bracket_rate)
        return full_amounts
    
    def build_rates_list(self) -> list:
        """ Build incremental quantity of money with rate

        :return: list of bracket income size and rate
        :rtype: list
        """
        taxed_amounts = []
        for index, bracket in enumerate(self.tax_brackets):
            try:
                taxed_amounts.append((self.tax_brackets[index+1]["bottom_of_range"] - bracket["bottom_of_range"], bracket["rate"]))
            except IndexError:
                taxed_amounts.append((100000000000.0, bracket["rate"]))
        return taxed_amounts

    def calculate_taxes(self, year: int) -> Transaction:        
        """Calculate taxes owed on income

        :return: taxes owed based on income
        :rtype: float
        """
        balance = self.yearly_taxable_income[year]
        taxes_owed = 0.0
        bracket_index = 0
        for deduction in self.deductions:
            if deduction.executable(year):
                self.yearly_deductions[year] += deduction.get_amount(year)
        balance -= self.yearly_deductions[year]
        while balance > 0.0:
            if balance > self.taxed_amounts[bracket_index][0]:
                taxes_owed += self.full_amounts[bracket_index]
                balance -= self.taxed_amounts[bracket_index][0]
            else:
                taxes_owed += balance * self.taxed_amounts[bracket_index][1]
                balance -= balance
            bracket_index += 1
        self.yearly_taxes_owed[year] = taxes_owed
        taxes_owed = taxes_owed + self.yearly_taxes_prepaid[year]
        for credit in self.credits:
            if credit.executable(year):
                self.yearly_credits[year] += credit.get_amount(year)
        taxes_owed -= self.yearly_credits[year]
        self.yearly_tax_bill[year] = taxes_owed
        deposit = False
        if taxes_owed < 0.0:
            deposit = True
            taxes_owed = abs(taxes_owed)
        return_transaction = Transaction(
            name=f"{year} Federal Income Taxes",
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
        return [
            {
                "year": y,
                "taxable_income": round(Decimal(self.yearly_taxable_income[y])),
                "taxes_owed": round(Decimal(self.yearly_taxes_owed[y])),
                "taxes_prepaid": round(Decimal(self.yearly_taxes_prepaid[y])),
                "deductions": round(Decimal(self.yearly_deductions[y])),
                "credits": round(Decimal(self.yearly_credits[y])),
                "tax_bill": round(Decimal(self.yearly_tax_bill[y])),
            } for y in self.yearly_tax_bill
        ]