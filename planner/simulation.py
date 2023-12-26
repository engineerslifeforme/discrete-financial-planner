from datetime import date
from dateutil.relativedelta import relativedelta 

from pydantic import BaseModel
from typing import List

from planner.asset import Asset
from planner.interest_rate import InterestRate
from planner.common import DEFAULT_INTEREST
from planner.transaction import Transaction

class Simulation(BaseModel):
    start: date
    end: date
    assets: List[Asset] = []
    interest_rates: List[InterestRate] = []
    transactions: List[Transaction] = []

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
        self.interest_rates.append(InterestRate(name=DEFAULT_INTEREST))
        interest_rate_dict = {i.name: i for i in self.interest_rates}
        for asset in self.assets:
            asset.get_interest_rate(interest_rate_dict)
        asset_dict = {a.name: a for a in self.assets}
        for transaction in self.transactions:
            transaction.setup(self.start, self.end, asset_dict, interest_rate_dict)

    def run(self) -> int:
        """ Run simulation from start to end

        :return: number of days in simulation execution
        :rtype: int

        Each day:

        1. Execute Transactions
        2. Mature Assets

        Capture asset state monthly
        """
        current_date = self.start
        current_month = self.start.month
        days = 0
        asset_states = []
        while current_date <= self.end:
            next_date = current_date + relativedelta(days=1)
            last_day_of_month = False
            if next_date.month != current_month:
                last_day_of_month = True

            for transaction in self.transactions:
                if transaction.executable(current_date):
                    if transaction.source is not None:
                        transaction.source.execute_transaction(transaction, False, current_date)
                    if transaction.destination is not None:
                        transaction.destination.execute_transaction(transaction, True, current_date)
            
            for asset in self.assets:
                asset.mature()
                if last_day_of_month:                    
                    asset_states.append(asset.get_state(current_date))
            
            current_date = next_date
            current_month = current_date.month            
            days += 1
        return days, asset_states

