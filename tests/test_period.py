from datetime import date

import pytest

from planner.period import (
    DailyFrequency,
    WeeklyFrequency,
    BiweeklyFrequency,
    MonthlyFrequency,
)
from planner.util import ONE_DAY

@pytest.fixture
def default_start():
    return date(date.today().year, 1, 1)

def test_daily_valid():
    df = DailyFrequency(frequency="Daily")
    assert(df.is_valid(date.today()))

def test_defaults(default_start):
    df = DailyFrequency(frequency="Daily")
    assert(df.first_date == default_start)
    assert(df.every_x_periods == 1)

    adate = date(2024,2,1)
    df = DailyFrequency(
        frequency="Daily",
        start=adate,
    )
    assert(df.first_date == adate)

def test_periods(default_start):
    start = default_start
    df = DailyFrequency(
        frequency="Daily",
        every_x_periods=2,
        start=start,
    )
    assert(df.is_valid(start))
    assert(not df.is_valid(start + ONE_DAY))
    assert(df.is_valid(start + ONE_DAY * 2))
    assert(not df.is_valid(start + ONE_DAY * 3))
    assert(df.is_valid(start + ONE_DAY * 4))

def test_weekly(default_start):
    wf = WeeklyFrequency(
        frequency="Weekly",
    )
    assert(wf.is_valid(default_start))
    assert(not wf.is_valid(default_start + ONE_DAY))
    assert(wf.is_valid(default_start + ONE_DAY * 7))
    
def test_biweekly(default_start):
    wf = BiweeklyFrequency(
        frequency="Biweekly",
    )
    assert(wf.is_valid(default_start))
    assert(not wf.is_valid(default_start + ONE_DAY))
    assert(not wf.is_valid(default_start + ONE_DAY * 7))
    assert(wf.is_valid(default_start + ONE_DAY * 14))

def test_montly(default_start):
    adate = date(2024,3,1)
    wf = MonthlyFrequency(
        frequency="Monthly",
    )
    assert(wf.is_valid(adate))
    assert(not wf.is_valid(adate + ONE_DAY))
    assert(wf.is_valid(date(2024, 4, 1)))


def test_load_dates():
    df = DailyFrequency(
        frequency="Daily",
        start="a",
        end="b",
    )
    adate = date(2024,5,1)
    bdate = date(2024,6,1)
    df.load_dates({"a": adate, "b": bdate})
    assert(df.start == adate)
    assert(df.end == bdate)
    assert(df.first_date == adate)