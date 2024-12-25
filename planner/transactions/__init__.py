from typing import Union

from planner.transactions.transaction import (
    DailyTransaction,
    WeeklyTransaction,
    BiweeklyTransaction,
    MonthlyTransaction,
    YearlyTransaction,
)

transaction_options = Union[
    DailyTransaction,
    WeeklyTransaction,
    BiweeklyTransaction,
    MonthlyTransaction,
    YearlyTransaction,
]
