from datetime import date

from planner.transaction import Transaction, FrequencyEnum

def test_executable():
    transaction = Transaction(
        name='a',
        start=date(2023,12,25),
        end=date(2024,12,25),
    )
    # Must be between start and end
    assert(not transaction.executable(date(2023,12,24)))
    assert(not transaction.executable(date(2024,12,26)))
    # Must only start on start
    assert(not transaction.executable(date(2023,12,26)))
    # Monthly only occurs on day
    assert(transaction.executable(date(2023,12,25)))
    assert(not transaction.executable(date(2023,12,26)))
    assert(transaction.executable(date(2024,1,25)))
    assert(transaction.executable(date(2024,12,25)))
    # Won't execute twice
    assert(not transaction.executable(date(2024,12,25)))