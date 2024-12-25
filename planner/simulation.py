from datetime import date, timedelta
from typing import Optional, Dict
from pathlib import Path

from pydantic import BaseModel
from tqdm import tqdm
import yaml
from loguru import logger

from planner.action_manager import ActionManager
from planner.interest_rates.basic import BasicInterestRate
from planner.assets.asset import NotAllowedNegativeBalance

ONE_DAY = timedelta(days=1)

class Simulation(BaseModel):
    start: Optional[date] = date.today()
    end: Optional[date] = date.today() + timedelta(weeks=52 * 10)
    action_manager: ActionManager
    labeled_dates: Optional[Dict[str, date]] = {}
    interest_rates: Optional[Dict[str, BasicInterestRate]] = {}
    config_path: Optional[Path] = None # Should be private

    def model_post_init(self, __context):
        if self.config_path is not None:
            self.action_manager.load_paths(root=self.config_path.parent)
        self.action_manager.load_dates(self.labeled_dates)
        self.action_manager.load_interest_rates(self.interest_rates)

    def run(self):
        day_quantity = (self.end - self.start).days
        current_date = self.start
        current_month = self.start.month
        complete = True
        for day_index in tqdm(range(day_quantity), desc="Running simulation"):
            try:
                self.action_manager.day_iterate(current_date, day_index)
            except NotAllowedNegativeBalance as e:
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

    @classmethod
    def file_load(cls, file_path: Path):
        data = yaml.safe_load(file_path.read_text())
        data["config_path"] = file_path
        sim = cls(**data)        
        return sim

if __name__ == "__main__":
    sim = Simulation.file_load(Path("new_private.yml"))
    sim.run()
    print("here")