from decimal import Decimal

from planner.interest_rate import InterestRate
from planner.common import ZERO

def test_interest_rate():
    interest_rate = InterestRate(name="test")
    assert(interest_rate.rate == 0.0)

    new_rate = 7.0
    interest_rate = InterestRate(name="test", rate=new_rate)
    assert(interest_rate.rate == new_rate)

def test_daily_rate():
    new_rate = 7.0
    interest_rate = InterestRate(name="test", rate=new_rate)
    assert(interest_rate.daily_rate == (new_rate / 100.0) / 365.0)