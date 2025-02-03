import math
from dataclasses import dataclass
from enum import Enum
from datetime import date

from planner.transactions.life_expectancy import LIFE_EXPECTANCY
from planner.transactions.transaction import Transaction, TransactionInput
from planner.period import FrequnecyEnum

# def annuitization(balance: float, age: int, afr: float):
#     return (balance / LIFE_EXPECTANCY[age]) * afr

def amortization(balance: float, age: int, afr: float):
    num = balance * afr
    denom = 1 - math.pow((1 + afr), (-1.0 * LIFE_EXPECTANCY[age]))
    return num / denom

def rmd(balance: float, age: int):
    return balance / LIFE_EXPECTANCY[age]

class SeppMethodsEnum(str, Enum):
    amortization = "amortization"
    rmd = "rmd"

@dataclass
class Sepp(Transaction):
    sepp_method: SeppMethodsEnum
    sepp_rate: float
    sepp_start_age: int
    _amortization_amount: float = None
    _source_empty: bool = False

    def _get_amount(self, *args):
        amount = None
        if self.sepp_method == SeppMethodsEnum.amortization:
            if self._amortization_amount is None:
                self._amortization_amount = amortization(self.source.current_balance, self.sepp_start_age, self.sepp_rate / 100.0)
            amount = self._amortization_amount
        elif self.sepp_method == SeppMethodsEnum.rmd:
            # Not sure if you use the start age each time or not
            amount = rmd(self.source.current_balance, self.sepp_start_age)
        else:
            raise ValueError(f"Unknown sepp method: {self.sepp_method}")
        if amount > self.source.current_balance:
            amount = self.source.current_balance
            self._source_empty = True
        return amount

    def is_valid(self, current_date):
        valid =  super().is_valid(current_date)
        return valid and not self._source_empty


class SeppInput(TransactionInput):
    sepp_method: SeppMethodsEnum
    sepp_rate: float
    sepp_start_age: int

    @property
    def _destination_class(self):
        return Sepp    
    
    def model_post_init(self, __context) -> None:
        assert(self.source is not None), "Sepp must have source"
        assert(self.destination is not None), "Sepp must have destination"
        assert(self.frequency == FrequnecyEnum.yearly), "Sepp payments must have a yearly frequency"
        if self.start is not None and self.end is not None:
            assert((self.end - self.start) >= (365 * 5)), "Sepp must last at least 5 years"

if __name__ == "__main__":
    balance = 250000
    # print(annuitization(250000, 53, 0.015))
    print(amortization(250000, 53, 0.015))
    print(rmd(250000, 53))
    # print(annuitization(100000, 50, 0.035))
    print(amortization(100000, 50, 0.035))
    print(rmd(100000, 50))
    print("done")