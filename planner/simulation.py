from datetime import date
from dateutil.relativedelta import relativedelta 

from pydantic import BaseModel
from typing import List, Dict
from tqdm import tqdm

from planner.asset import Asset
from planner.interest_rate import InterestRate
from planner.common import DEFAULT_INTEREST, ZERO
from planner.transaction import Transaction, InsufficientBalanceException
from planner.mortgage import Mortgage
from planner.income_taxes import IncomeTaxCaculator
from planner.action_log import ActionLog

ZERO_INTEREST_RATE = InterestRate(name=DEFAULT_INTEREST)

class ActionLogger:

    def __init__(self):
        self.action_logs = {}
        self.year = None

    def set_year(self, year: int):
        """ set year on logger

        :param year: year of action(s)
        :type year: int
        """
        self.year = year
        self.action_logs[self.year] = []

    def add_action_log(self, action_log: ActionLog):
        """ Assess and add action log to list if good

        :param action_log: action log dictionary
        :type action_log: ActionLog

        We don't want $0.00 actions
        """
        if action_log.amount == ZERO:
            return
        self.action_logs[self.year].append(action_log)

    def flatten_logs(self) -> list:
        sorted_years = list(self.action_logs.keys())
        sorted_years.sort()
        flat_list = []
        for key in sorted_years:
            flat_list.extend([
                l.to_dict() for l in self.action_logs[key]
            ])
        return flat_list

class Simulation(BaseModel):
    start: date
    end: date
    assets: List[Asset] = []
    interest_rates: List[InterestRate] = []
    transactions: List[Transaction] = []
    dates: Dict[str, date] = {}
    mortgages: List[Mortgage] = []
    federal_income_taxes: IncomeTaxCaculator = None
    state_income_taxes: IncomeTaxCaculator = None

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
            self.federal_income_taxes.setup(asset_dict, self.start.year)        
            self.federal_income_taxes.get_interest_rate(interest_rate_dict)
        if self.state_income_taxes is not None:
            self.state_income_taxes.setup(asset_dict, self.start.year)
            self.state_income_taxes.get_interest_rate(interest_rate_dict)

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
        action_logger.set_year(current_date.year)
        error_raised = None
        mortgage_interest = 0.0
        networth_list = []
        #import pdb;pdb.set_trace()
        #while current_date <= self.end and error_raised is None:
        for _ in tqdm(range((self.end - self.start).days), desc="Running simulation for each day..."):
            next_date = current_date + relativedelta(days=1)
            last_day_of_month = False
            year_ended = False
            if next_date.month != current_month:
                last_day_of_month = True
            if next_date.year != current_date.year:
                year_ended = True
            for transaction in self.transactions:
                if transaction.executable(current_date):
                    # Order is important here, change destination then source
                    # transaction amount is sometimes based on source balance
                    try:
                        if transaction.destination is not None:
                            _, _, transaction_log = transaction.destination.execute_transaction(transaction, True, current_date)
                            action_logger.add_action_log(transaction_log)
                        if transaction.source is not None:
                            _, _, transaction_log = transaction.source.execute_transaction(transaction, False, current_date)
                            action_logger.add_action_log(transaction_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
            
            for mortgage in self.mortgages:
                if mortgage.executable(current_date):
                    # Order is important here, change source then destination
                    # mortgage amount based on remaining balance of debt, so change debt second
                    try:
                        mortgage_interest += mortgage.payment_interest
                        _, _, mortgage_log = mortgage.source.execute_transaction(mortgage, False, current_date)
                        action_logger.add_action_log(mortgage_log)
                        _, _, mortgage_log = mortgage.destination.execute_transaction(mortgage, True, current_date)
                        action_logger.add_action_log(mortgage_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
            
            if year_ended:
                if self.federal_income_taxes is not None:
                    tax_transaction, deposit = self.federal_income_taxes.calculate_taxes(
                        action_logger.action_logs[current_date.year], 
                        current_date.year,
                        True,
                        mortgage_interest,
                    )
                    # Pydantic won't allow direct assignment
                    # the way the delayed assignment is handled
                    tax_transaction.interest_rate = ZERO_INTEREST_RATE
                    try:
                        _, _, transaction_log = tax_transaction.source.execute_transaction(tax_transaction, deposit, current_date)
                        action_logger.add_action_log(transaction_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
                if self.state_income_taxes is not None:
                    tax_transaction, deposit = self.state_income_taxes.calculate_taxes(
                        action_logger.action_logs[current_date.year],
                        current_date.year,
                        False,
                        mortgage_interest,
                    )
                    # Pydantic won't allow direct assignment
                    # the way the delayed assignment is handled
                    tax_transaction.interest_rate = ZERO_INTEREST_RATE
                    try:
                        _, _, transaction_log = tax_transaction.source.execute_transaction(tax_transaction, deposit, current_date)
                        action_logger.add_action_log(transaction_log)
                    except InsufficientBalanceException as e:
                        error_raised = e
                        break
                action_logger.set_year(next_date.year)
                mortgage_interest = 0.0
            
            if last_day_of_month:
                asset_total = ZERO
                liability_total = ZERO
                for asset in self.assets:                                        
                    asset_states.append(asset.get_state(current_date))
                    asset_balance = asset.get_balance()
                    if asset_balance >= ZERO:
                        asset_total += asset_balance
                    else:
                        liability_total += asset_balance
                networth_list.append({
                    "type": "assets",
                    "balance": asset_total,
                    "date": current_date
                })
                networth_list.append({
                    "type": "liabilities",
                    "balance": liability_total,
                    "date": current_date
                })
                networth_list.append({
                    "type": "networth",
                    "balance": asset_total + liability_total,
                    "date": current_date
                })
            
            current_date = next_date
            current_month = current_date.month            
            days += 1

        if error_raised is not None:
            print("Simulation was unable to complete due to error:")
            print(error_raised)
        print("Summarizing simulation results...")
        if self.federal_income_taxes is not None:
            fed_tax_data = self.federal_income_taxes.summarize()
        else:
            fed_tax_data = None
        if self.state_income_taxes is not None:
            state_tax_data = self.state_income_taxes.summarize()
        else:
            state_tax_data = None
        return days, asset_states, action_logger.flatten_logs(), fed_tax_data, state_tax_data, networth_list
