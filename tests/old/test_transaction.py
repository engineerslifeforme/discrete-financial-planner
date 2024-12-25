from datetime import date

from planner.transaction import Transaction, TransactionGroup

def test_executable():
    transaction = Transaction(
        name='a',
        start_date=date(2023,12,25),
        end_date=date(2024,12,25),
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

def test_nesting():
    tg = TransactionGroup(**{
        "name": "a",
        "start_date": date(2023,1,1),
        "sub_transactions": [
            {
                "name": "b",
                "start_date": date(2025,1,1),
            },
        ]
    })
    tg.to_transaction_list()

    tg = TransactionGroup(**{
        "name": "a",
        "start_date": date(2023,1,1),
        "end_date": date(2026,1,1),
        "sub_transactions": [
            {
                "name": "d",
                "destination": "DEF",
            },
            {
                "name": "b",
                "start_date": date(2025,1,1),
                "sub_transactions": [
                    {"name": "c"},
                ],
            },
        ]
    })
    tg.to_transaction_list()
    print("complete")