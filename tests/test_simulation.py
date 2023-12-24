from datetime import date

import yaml

from planner import Simulation

def test_simulation():
    simulation = Simulation(**yaml.safe_load("""start: 2023-01-01
end: 2024-01-01"""))
    assert(simulation.start == date(2023, 1, 1))
    assert(simulation.end == date(2024, 1, 1))