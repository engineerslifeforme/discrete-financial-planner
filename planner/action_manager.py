from typing import Optional, List, Union
from datetime import date
from pathlib import Path
import csv

from pydantic import BaseModel

from planner.transactions import transaction_options
from planner.assets import asset_options, AssetLog
from planner.assets.asset import NotAllowedNegativeBalance
from planner.util import load_list_path
from planner.action import Action

class ActionManager(BaseModel):
    assets: Optional[List[Union[asset_options, Path]]] = []
    transactions: Optional[List[Union[transaction_options, Path]]] = []
    
    def model_post_init(self, __context) -> None:
        self._build_asset_map()
        self._action_log_file = open("action_log.csv", "w")
        self._action_log = csv.DictWriter(
            self._action_log_file, 
            fieldnames=list(Action.model_fields.keys()) + ["date"])
        self._action_log.writeheader()
        self._asset_log_file = open("asset_log.csv", "w")
        self._asset_log = csv.DictWriter(
            self._asset_log_file, 
            fieldnames=list(AssetLog.model_fields.keys()) + ["date"])
        self._asset_log.writeheader()

    def _build_asset_map(self):
        self._asset_map = {a.name: a for a in self.assets}
    
    def save_state(self, date: date):
        for asset in self.assets:
            data = asset.log.model_dump()
            data["date"] = date
            self._asset_log.writerow(data)
    
    def load_paths(self, **kwargs):
        self.transactions = load_list_path(
            self.transactions,
            transaction_options,
            **kwargs,
        )
        self.assets = load_list_path(
            self.assets,
            asset_options,
            **kwargs,
        )
        self._build_asset_map()
    
    def load_dates(self, *args, **kwargs):
        for transaction in self.transactions:
            transaction.load_dates(*args, **kwargs)

    def load_interest_rates(self, *args, **kwargs):
        for transaction in self.transactions:
            transaction.load_interest_rate(*args, **kwargs)

    def day_iterate(self, current_date: date, days: int):
        action_list = []
        for transaction in self.transactions:
            if transaction.is_valid(current_date):
                action_list.extend(transaction.get_actions(days))
        action_list.sort(key=lambda x: x.priority)
        for action in action_list:
            if action.empty_source:
                action.amount = self._asset_map[action.source_name].current_balance
            try:
                if action.source_name is not None:
                    self._asset_map[action.source_name].withdraw(action.amount)
                if action.destination_name is not None:
                    self._asset_map[action.destination_name].deposit(action.amount)
                action_log_data = action.model_dump()
                action_log_data["date"] = current_date
                self._action_log.writerow(action_log_data)
            except NotAllowedNegativeBalance:
                raise
        
    def close_log(self):
        self._action_log_file.close()

if __name__ == "__main__":
    am = ActionManager()
    am = ActionManager(assets=["a.yml"])
    print("here")