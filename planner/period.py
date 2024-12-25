from datetime import date
from typing import Optional, Literal, Union, Annotated

from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator

class PeriodModel(BaseModel):
    start: Optional[Union[date, str]] = None
    end: Optional[Union[date, str]] = None

    def is_time_valid(self, current_date: date) -> bool:
        valid = True
        if self.start is not None:
            valid = valid and current_date >= self.start
        if self.end is not None:
            valid = valid and current_date <= self.end
        return valid
    
    def load_dates(self, labeled_dates: dict):
        if type(self.start) == str:
            self.start = labeled_dates[self.start]
        if type(self.end) == str:
            self.end = labeled_dates[self.end]
    
class FrequencyModel(PeriodModel):
    frequency: str
    first_date: Optional[date] = None
    every_x_periods: int = 1
    _period_count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self._set_first_date()
        if self.every_x_periods is None:
            self.every_x_periods = 1
        
    def _set_first_date(self):
        set = False
        if self.first_date is None:
            set = True
        elif type(self.first_date) == str:
            set = True
        if set:
            if self.start is None:
                self.first_date = date(date.today().year, 1, 1)
            else:
                self.first_date = self.start

    def load_dates(self, *args, **kwargs):
        super().load_dates(*args, **kwargs)
        self._set_first_date()

    def is_period_good(self) -> bool:
        is_good = self._period_count >= self.every_x_periods
        if is_good:
            self._period_count = 0
        return is_good
    
    def is_valid(self, current_date: date) -> bool:
        if self.is_time_valid(current_date):
            self._period_count += 1
        return self.is_period_good()

class DailyFrequency(FrequencyModel):
    frequency: Literal["Daily"]

class WeeklyFrequency(FrequencyModel):
    frequency: Literal["Weekly"]

    def is_time_valid(self, current_date: date) -> bool:
        valid = super().is_time_valid(current_date)
        return valid and (((current_date - self.first_date).days % 7) == 0)

def check_two(v: int) -> None:
    assert(v == 2)

class BiweeklyFrequency(WeeklyFrequency):
    frequency: Literal["Biweekly"]
    every_x_periods: Optional[Annotated[int, AfterValidator(check_two)]] = 2

class MonthlyFrequency(FrequencyModel):
    frequency: Literal["Monthly"]

    def is_time_valid(self, current_date: date) -> bool:
        valid = super().is_time_valid(current_date)
        return valid and (current_date.day == self.first_date.day)
    
class YearlyFrequency(FrequencyModel):
    frequency: Literal["Yearly"]

    def is_time_valid(self, current_date: date) -> bool:
        valid = super().is_time_valid(current_date)
        return valid and (current_date.day == self.first_date.day) and (current_date.month == self.first_date.month)
    