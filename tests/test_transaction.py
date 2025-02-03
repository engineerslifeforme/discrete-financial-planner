from datetime import date

import pytest

from planner.transactions import Transaction
from planner.util import ZERO
from planner.interest_rates import BasicInterestRate

@pytest.fixture
def default_daily_transaction():
    return DailyTransaction(
        name="test daily",
        frequency="Daily",
    )

def test_default_daily(default_daily_transaction):
    ddt = default_daily_transaction
    assert(type(ddt) == DailyTransaction)
    assert(ddt.start is None)
    assert(ddt.end is None)
    assert(ddt.base_amount == ZERO)
    assert(ddt.source_name is None)
    assert(ddt.destination_name is None)
    assert(ddt.interest_rate is None)
    assert(ddt.priority == 100)
    assert(not ddt.empty_source)

def test_get_actions(default_daily_transaction):
    ddt = default_daily_transaction
    actions = ddt.get_actions(1)
    assert(len(actions) == 1)

    action = actions[0]
    assert(action.description == ddt.name)
    assert(action.amount == ddt.base_amount)
    assert(action.priority == ddt.priority)
    assert(action.source_name is None)
    assert(action.destination_name is None)
    assert(not action.empty_source)

def test_load_interest_rate():
    ir = BasicInterestRate(
        interest_type = "basic",
        year_rate_percentage=3.0,
    )
    dt = DailyTransaction(
        name="test daily",
        frequency="Daily",
        base_amount=100.00,
        interest_rate="test_ir",
    )
    dt.load_interest_rate({"test_ir": ir})
    assert(dt.interest_rate == ir)

def test_interest_amount():
    dt = DailyTransaction(
        name="test daily",
        frequency="Daily",
        base_amount=100.00,
        interest_rate=BasicInterestRate(
            interest_type = "basic",
            year_rate_percentage=3.65,
        ),
    )
    assert(dt.get_actions(1)[0].amount == 101.00)