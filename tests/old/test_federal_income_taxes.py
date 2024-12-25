from planner.income_taxes import IncomeTaxCaculator

def test_FederalIncomeTaxCaculator():
    calculator = IncomeTaxCaculator()
    taxes = calculator.calculate_taxes(100.00)
    assert(taxes == 10.00)
    taxes = calculator.calculate_taxes(11700.00)
    assert(taxes == 1160.0 + 12.0)