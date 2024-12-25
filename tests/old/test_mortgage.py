from decimal import Decimal

import yaml

from planner.mortgage import Mortgage
from planner.asset import Asset

def test_mortgage():
    mortgage = Mortgage(**yaml.safe_load("""name: a
loan_amount: 460000.00
loan_rate: 2.99
term_months: 180
remaining_balance: 460000.00
"""))
    mortgage.destination = Asset(
        name="a",
        balance = Decimal("-460000.00"),
        allow_negative_balance=True,
    )
    # Accounting for float math
    assert(
        abs(mortgage.get_amount(None, False) - 3174.46) < 0.01
    )
    assert(
        abs(mortgage.get_amount(None, True) - 2028.29) < 0.01
    )
    while mortgage.destination.f_balance < 0.0:
        mortgage.destination.execute_transaction(
            mortgage, True, None
        )