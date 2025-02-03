from datetime import date, timedelta
from typing import Optional, Dict, Union, List
from pathlib import Path
from dataclasses import dataclass
import time

from pydantic import BaseModel, field_serializer
from tqdm import tqdm
import yaml
from loguru import logger

from planner.action_manager import ActionManager, ActionManagerInput
from planner.interest_rates import interest_rate_options, interest_rate_input_options
from planner.assets.asset import NotAllowedNegativeBalance
from planner.util import ONE_DAY
from planner.plan_editor import PlanEditor

def yaml_load(file_path: Path) -> dict:
    data = yaml.safe_load(file_path.read_text())
    data["config_path"] = file_path
    return data

@dataclass
class Simulation:
    start: Optional[date]
    end: Optional[date]
    action_manager: ActionManager
    labeled_dates: Optional[Dict[str, date]]
    interest_rates: Optional[Dict[str, interest_rate_options]]
    config_path: Optional[Path] = None # Should be private

    def __post_init__(self):
        self.action_manager.load_dates(self.labeled_dates)
        self.action_manager.load_interest_rates(self.interest_rates)
        for _, ir in self.interest_rates.items():
            ir.initialize(self.start)

    def run(self):
        start = time.time()
        day_quantity = (self.end - self.start).days
        current_date = self.start
        current_month = self.start.month
        complete = True
        for day_index in tqdm(range(day_quantity), desc="Running simulation"):
            try:
                self.action_manager.day_iterate(current_date, day_index)
            except NotAllowedNegativeBalance as e:
                self.action_manager.save_state(current_date - ONE_DAY)
                logger.error(e)
                logger.error(f"Simulation ended early: day {day_index} {current_date}")
                complete = False
                break
            current_date += ONE_DAY
            if current_date.month != current_month:
                self.action_manager.save_state(current_date - ONE_DAY)
            current_month = current_date.month
        if complete:
            logger.info(f"Complete simulation: {day_quantity} days")
        self.action_manager.close_log()
        logger.info(f"Simulation duration: {time.time() - start} seconds")

class SimulationInput(BaseModel):
    start: Optional[date] = date.today()
    end: Optional[date] = date.today() + timedelta(weeks=52 * 10)
    action_manager: ActionManagerInput
    labeled_dates: Optional[Dict[str, date]] = {}
    interest_rates: Optional[Dict[str, interest_rate_input_options]] = {}
    config_path: Optional[Path] = None # Should be private

    def model_post_init(self, __context):
        if self.config_path is not None:
            self.action_manager.load_paths(root=self.config_path.parent)
    
    def to_dc_model(self) -> Simulation:
        data = self.model_dump()
        data.pop("action_manager", None)
        data.pop("interest_rates", None)
        action_manager = self.action_manager.to_dc_model()
        irs = {}
        for name, rate in self.interest_rates.items():
            irs[name] = self.interest_rates[name].to_dc_model()
        return Simulation(
            action_manager=action_manager,
            interest_rates=irs,
            **data,
        )
    
    @field_serializer('config_path')
    def serialize_config_path(self, config_path: Path):
        return str(config_path)
    
    def dump_sim(self) -> dict:
        return self.model_dump()
    
class DeltaSimulation(BaseModel):
    base_simulation_path: Path
    deltas: Dict[str, Union[str, date, float]] = {}
    transaction_adds: List[Dict[str, Union[str, date, float]]] = []
    asset_adds: List[Dict[str, Union[str, date, float]]] = []
    date_adds: Dict[str, date] = {}
    config_path: Path = None
    _sim: SimulationInput = None

    def model_post_init(self, __context):
        full_base_path = self.config_path.parent / self.base_simulation_path
        # Fully loading to resolve paths
        data = Input(input=yaml_load(full_base_path)).input.dump_sim()
        data["action_manager"]["transactions"].extend(self.transaction_adds)
        data["action_manager"]["assets"].extend(self.asset_adds)
        data["labeled_dates"].update(self.date_adds)
        pe = PlanEditor(data)
        for yaml_path, new_value in self.deltas.items():
            pe.set_value(yaml_path, new_value)        
        self._sim = SimulationInput(**pe.data)

    def to_dc_model(self) -> Simulation:
        return self._sim.to_dc_model()
    
    def dump_sim(self) -> dict:
        return self._sim.model_dump()
    
class Input(BaseModel):
    input: Union[SimulationInput, DeltaSimulation]

    @classmethod
    def file_load(cls, file_path: Path):
        data = yaml_load(file_path)
        sim = cls(input=data)        
        return sim.input.to_dc_model()

if __name__ == "__main__":
    import sys
    #path = Path(sys.argv[1])
    path = Path("payne_private_20250111/base_plan/new_private.yml")
    # path = Path("payne_private_20250111/early_3.yml")
    sim = Input.file_load(path)
    sim.run()
    #print("here")