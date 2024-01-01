from datetime import date
from dateutil.relativedelta import relativedelta 

from pydantic import BaseModel
from typing import List, Dict

from planner.asset import Asset
from planner.interest_rate import InterestRate
from planner.common import DEFAULT_INTEREST, ZERO
from planner.transaction import Transaction, InsufficientBalanceException
from planner.mortgage import Mortgage
from planner.federal_income_taxes import FederalIncomeTaxCaculator

ZERO_INTEREST_RATE = InterestRate(name=DEFAULT_INTEREST)

class ActionLogger:

    def __init__(self):
        self.action_logs = []

    def add_action_log(self, action_log: dict):
        """ Assess and add action log to list if good

        :param action_log: action log dictionary
        :type action_log: dict

        We don't want $0.00 actions
        """
        if action_log["amount"] == ZERO:
            return
        self.action_logs.append(action_log)

def combine_configs(config_list: list) -> dict:
    """ Combines multiple potentially subset dicts to a single

    :param config_list: multiple subset dictionaries
    :type config_list: list
    :return: single combined dictionary of data
    :rtype: dict
    """
    simple_keys = ["start", "end"]
    list_keys = [
        "transactions",
        "mortgages",
        "interest_rates",
        "assets",
    ]
    skeleton = {k: [] for k in list_keys}
    skeleton["dates"] = {}
    for s in simple_keys:
        skeleton[s] = None
    for c in config_list:
        try:
            skeleton["federal_income_taxes"] = c["federal_income_taxes"]
        except KeyError:
            pass
        try:
            skeleton["dates"].update(c["dates"])
        except KeyError:
            pass
        for s in simple_keys:
            try:
                skeleton[s] = c[s]
            except KeyError:
                pass
        for l in list_keys:
            try:
                skeleton[l].extend(c[l])
            except KeyError:
                pass
    return skeleton

class Simulation(BaseModel):
    start: date
    end: date
    assets: List[Asset] = []
    interest_rates: List[InterestRate] = []
    transactions: List[Transaction] = []
    dates: Dict[str, date] = {}
    mortgages: List[Mortgage] = []
    federal_income_taxes: FederalIncomeTaxCaculator = None

    def __init__(self, *args, **kwargs):
        """Initialization with setup

        Additional setup needed to link internal data
        structures, so simple overload of __init__
        """
        super().__init__(*args, **kwargs)
        self.setup()
    
    def setup(self):
        """Setup any linkages between objects
        """
        # Setup defualt 0 interest rate
        self.interest_rates.append(ZERO_INTEREST_RATE)
        interest_rate_dict = {i.name: i for i in self.interest_rates}
        # for asset in self.assets:
        #     asset.get_interest_rate(interest_rate_dict)
        asset_dict = {a.name: a for a in self.assets}
        for transaction in self.transactions:
            transaction.setup(self.start, self.end, asset_dict, interest_rate_dict, self.dates)
        for mortgage in self.mortgages:
            mortgage.setup(self.start, self.end, asset_dict, interest_rate_dict, self.dates)
        if self.federal_income_taxes is not None:
            self.federal_income_taxes.setup(asset_dict)        

    def run(self) -> tuple:
        """ Run simulation from start to end

        :return: number of days in simulation execution, periodic asset state, change logs
        :rtype: tuple

        Each day:

        1. Execute Transactions
        2. Execute Mortgages
        3. Mature Assets

        Capture asset state monthly
        """
        current_date = self.start
        current_month = self.start.month
        days = 0
        asset_states = []
        action_logger = ActionLogger()
        error_raised = None
        if self.federal_income_taxes is not None:
            self.federal_income_taxes.new_year(current_date.year)
        while current_date <= self.end and error_raised is None:
            next_date = current_date + relativedelta(days=1)
            last_day_of_month = False
            year_ended = False
            if next_date.month != current_month:
                last_day_of_month = True
            if next_date.year != current_date.year:
                if self.federal_income_taxes is not None:
                    self.federal_income_taxes.new_year(next_date.year)
                year_ended = True
            for transaction in self.transactions:
                if transaction.executable(current_date):
                    # Order is important here, change destination then source
                    # transaction amount is sometimes based on source balance
                    try:
                        if transaction.destination is not None:
                            _, transaction_amount, transaction_log = transaction.destination.execute_transaction(transaction, True, current_date)
                            action_logger.add_action_log(transaction_log)
                            if transaction.income_taxable and self.federal_income_taxes is not None:
                                self.federal_income_taxes.update_taxable_income(current_date.year, transaction_amount)
                        if transaction.source is not None:
                            _, transaction_amount, transaction_log = transaction.source.execute_transaction(transaction, False, current_date)
                            action_logger.add_action_log(transaction_log)
                            if self.federal_income_taxes is not None:
                                if transaction.income_tax_payment:
                                    self.federal_income_taxes.update_taxes_paid(current_date.year, transaction_amount)
                                if transaction.tax_deductable:
                                    self.federal_income_taxes.update_deductions(current_date.year, abs(transaction_amount))
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
            
            for mortgage in self.mortgages:
                if mortgage.executable(current_date):
                    # Order is important here, change source then destination
                    # mortgage amount based on remaining balance of debt, so change debt second
                    try:
                        if self.federal_income_taxes is not None:
                            self.federal_income_taxes.update_deductions(current_date.year, mortgage.payment_interest)
                        _, _, mortgage_log = mortgage.source.execute_transaction(mortgage, False, current_date)
                        action_logger.add_action_log(mortgage_log)
                        _, _, mortgage_log = mortgage.destination.execute_transaction(mortgage, True, current_date)
                        action_logger.add_action_log(mortgage_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
            
            if year_ended:
                if self.federal_income_taxes is not None:
                    tax_transaction, deposit = self.federal_income_taxes.calculate_taxes(current_date.year)
                    # Pydantic won't allow direct assignment
                    # the way the delayed assignment is handled
                    tax_transaction.interest_rate = ZERO_INTEREST_RATE
                    try:
                        _, _, transaction_log = tax_transaction.source.execute_transaction(tax_transaction, deposit, current_date)
                        action_logger.add_action_log(transaction_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
            
            for asset in self.assets:
                if last_day_of_month:                    
                    asset_states.append(asset.get_state(current_date))
            
            current_date = next_date
            current_month = current_date.month            
            days += 1

        if error_raised is not None:
            print("Simulation was unable to complete due to error:")
            print(error_raised)
        if self.federal_income_taxes is not None:
            tax_data = self.federal_income_taxes.summarize()
        else:
            tax_data = None
        return days, asset_states, action_logger.action_logs, tax_data
