from decimal import Decimal

from planner.common import InterestBaseModel, ZERO

class TaxDeduction(InterestBaseModel):
    amount: Decimal = ZERO
    start_year: int = None
    end_year: int = None

    def executable(self, year: int) -> bool:
        if self.end_year is None and self.start_year is None:
            return True
        elif self.end_year is None:
            return year >= self.start_year
        elif self.start_year is None:
            return year <= self.end_year
        else:
            return year >= self.start_year and year <= self.end_year
    
    def get_amount(self, year: int) -> float:
        # TODO: implement interest growth
        return float(self.amount)
