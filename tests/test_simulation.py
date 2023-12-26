from datetime import date
from decimal import Decimal

import yaml
import pytest

from planner import Simulation
from planner.common import round

BALANCE = "100.00"
RATE = "7.0"

@pytest.fixture
def simulation():
    return Simulation(**yaml.safe_load(f"""start: 2023-01-01
end: 2024-01-01
interest_rates:
    - name: example
      rate: 7.0
assets:
    - name: Bank
      balance: {BALANCE}
      interest_rate: example
"""))

INCREMENT = "50.00"

@pytest.fixture
def transaction_simulation():
    return Simulation(**yaml.safe_load(f"""start: 2023-01-01
end: 2024-01-01
transactions:
    - name: a
      amount: {INCREMENT}
      destination: Bank
assets:
    - name: Bank
      balance: {BALANCE}
"""))

def test_simulation(simulation):    
    assert(simulation.start == date(2023, 1, 1))
    assert(simulation.end == date(2024, 1, 1))

def test_run(simulation):
    days, _ = simulation.run()
    assert(days == 366) # 2024 leap year
    # Daily interest compounds a little differently
    # than the simply method below
    assert(
        abs(simulation.assets[0].balance - round(Decimal(BALANCE) + (Decimal(BALANCE) * (Decimal(RATE) / Decimal("100.00"))))) < Decimal("1.00")
    )

def test_transactions(transaction_simulation):
    transaction_simulation.run()
    assert(transaction_simulation.assets[0].balance == Decimal(BALANCE) + Decimal("13") * Decimal(INCREMENT))
