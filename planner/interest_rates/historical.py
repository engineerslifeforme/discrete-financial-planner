from dataclasses import dataclass
from typing import Literal, Optional, List
from decimal import Decimal
from datetime import date, datetime, timedelta
from pathlib import Path
import csv

import calendar

from planner.interest_rates.basic import BaseInterestRateInput, BaseInterestRate, BasicInterestRate
from planner.util import future_value, future_interest, interest_of_x, get_compounded_rate
from planner.interest_rates.interest_and_inflation import INTEREST_AND_INFLATION

def date_to_int(a_date: date) -> int:
    return _date_to_int(a_date.year, a_date.month)

def _date_to_int(year: int, month: int) -> int:
    return year * 12 + (month - 1)

@dataclass
class LookUpItem:
    ref_date: date
    daily: float
    daily_cumulative: float

@dataclass
class HistoricalInterestRate(BaseInterestRate):
    data_path: Path
    start_year: int = 1871
    start_month: int = 1
    _ir_lookup: Optional[List[LookUpItem]] = None

    def initialize(self, config_path: Path = None, simulation_start_date: date = None):
        requested_entries = []
        csv_reader = csv.DictReader((config_path / self.data_path).open("r"))
        data_start_date = date(self.start_year, self.start_month, 1)
        for row in csv_reader:
            date = datetime.strptime(row["Date"], "%Y-%m-%d").date()
            if date >= data_start_date:
                row["_date"] = date
                requested_entries.append(row)
        self._ir_lookup = []
        quantity_entries = len(requested_entries)
        
        index = 0
        current_sim_date = simulation_start_date
        current_sim_month = current_sim_date.month
        # 200 years of data should be enough
        start_balance = 1.0
        balance = start_balance
        days = 0
        while current_sim_date < date(simulation_start_date.year + 200, simulation_start_date.month, simulation_start_date.day):
            if current_sim_date.month != current_sim_month:
                index += 1
                current_sim_month = current_sim_date.month
            current_index = index
            while current_index > quantity_entries:
                current_index -= quantity_entries                
            current_entry = requested_entries[current_index]
            days_in_month = calendar.monthrange(current_sim_date.year, current_sim_date.month)[1]

            daily_interest = interest_of_x(current_entry["SP500"], days_in_month)
            balance += balance * daily_interest
            self._ir_lookup.append(LookUpItem(
                ref_date=current_sim_date,
                daily=daily_interest,
                daily_cumulative=get_compounded_rate(start_balance, balance, days)
            ))
            current_sim_date += timedelta(days=1)
            days += 1


        

class HistoricalInterestRateInput(BaseInterestRateInput):
    interest_type: Literal["historical"]
    data_path: Path

    @property
    def dc_type(self):
        return HistoricalInterestRate

if __name__ == "__main__":
    hist = HistoricalInterestRate(data_path=Path("datahub_io.csv"))
    hist.initialize(config_path=Path("."), simulation_start_date=date(2024, 1, 1))
    print("debug")