from datetime import date
from typing import Optional, Literal, Union, Annotated
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, field_serializer
from pydantic.functional_validators import AfterValidator

class FrequnecyEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    yearly = "yearly"

@dataclass
class PeriodModel:
    start: Optional[date]
    end: Optional[date]

    def _is_time_valid(self, current_date: date) -> bool:
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

class PeriodModelInput(BaseModel):
    start: Optional[Union[date, str]] = None
    end: Optional[Union[date, str]] = None
    
@dataclass
class FrequencyModel(PeriodModel):
    frequency: FrequnecyEnum
    first_date: Optional[date]
    every_x_periods: int

    def __post_init__(self):
        self._period_count = self.every_x_periods

    def load_dates(self, *args, **kwargs):
        super().load_dates(*args, **kwargs)
        self._set_first_date()
        
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

    def _is_period_good(self) -> bool:
        is_good = self._period_count >= self.every_x_periods
        if is_good:
            self._period_count = 0
        return is_good
    
    def is_valid(self, current_date: date) -> bool:
        time_valid = self._is_time_valid(current_date)
        if time_valid:
            self._period_count += 1
        return time_valid and self._is_period_good()
    
    def _is_time_valid(self, current_date):
        valid = super()._is_time_valid(current_date)
        if self.frequency == FrequnecyEnum.daily:
            pass
        elif self.frequency == FrequnecyEnum.weekly:
            valid = valid and (((current_date - self.first_date).days % 7) == 0)
        elif self.frequency == FrequnecyEnum.monthly:
            valid = valid and (current_date.day == self.first_date.day)
        elif self.frequency == FrequnecyEnum.yearly:
            valid = valid and (current_date.day == self.first_date.day) and (current_date.month == self.first_date.month)
        else:
            raise ValueError(f"Unknown Frequency Enum value: {self.frequency}")
        return valid

class FrequencyModelInput(PeriodModelInput):
    first_date: Optional[date] = None
    every_x_periods: int = 1
    frequency: FrequnecyEnum = FrequnecyEnum.daily

    @field_serializer('frequency')
    def serialize_frequency(self, frequency: FrequnecyEnum):
        return frequency.value

    