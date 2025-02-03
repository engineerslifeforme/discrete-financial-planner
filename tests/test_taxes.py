from planner.taxes import calculate_taxes

def test_calculate_taxes():
    assert(
        calculate_taxes(10000.0, 0.0) == 1000.0
    )
    answer = (11600 * .10) + (3000 * 0.12)
    assert(
        calculate_taxes(14600.0, 0.0) == answer
    )
    answer = (11600.0 * .10) + \
             ((47150.0 - 11600.0) * 0.12) + \
             ((100525.0 - 47150.0) * 0.22) + \
             ((191950.0 - 100525.0) * 0.24) + \
             ((243725.0 - 191950.0) * 0.32) + \
             ((609350.0 - 243725.0) * 0.35) + \
             ((1000000.0 - 609350.0) * 0.37)
    result = calculate_taxes(1000000.0, 0.0)
    assert(
        result == answer
    )