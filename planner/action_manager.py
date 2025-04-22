from typing import Optional, List, Union
from datetime import date
from pathlib import Path
import csv
from dataclasses import dataclass, fields as dc_fields

from pydantic import BaseModel, field_serializer
from loguru import logger

from planner.transactions import transaction_options, transaction_input_options
from planner.assets import asset_options, AssetLog, asset_input_options
from planner.assets.asset import NotAllowedNegativeBalance
from planner.util import load_list_path
from planner.action import Action
from planner.taxes import FederalTax, FederalTaxInput

@dataclass
class ActionManager:
    assets: List[asset_options]
    transactions: List[transaction_options]
    fed_tax_handler: Optional[FederalTax] = None

    def __post_init__(self):
        self._action_log_file = open("action_log.csv", "w")
        self._action_log = csv.DictWriter(
            self._action_log_file, 
            fieldnames=[f.name for f in dc_fields(Action)] + ["date"])
        self._action_log.writeheader()
        self._asset_log_file = open("asset_log.csv", "w")
        self._asset_log = csv.DictWriter(
            self._asset_log_file, 
            fieldnames=list(AssetLog.model_fields.keys()) + ["date"])
        self._asset_log.writeheader()
        self._actions_to_write = []
        self._build_asset_map()
        self.transactions.sort(key=lambda x: x.priority)
        self.load_assets()
        

    def load_assets(self):
        for transaction in self.transactions:
            transaction.load_assets(self._asset_map)
        if self.fed_tax_handler is not None:
            self.fed_tax_handler.transaction.load_assets(self._asset_map)
        

    def day_iterate(self, current_date: date, days: int):
        valid_transactions = [t for t in self.transactions if t.is_valid(current_date)]
        if self.fed_tax_handler is not None:
            if self.fed_tax_handler.is_tax_day(current_date):
                tax_transaction = self.fed_tax_handler.get_taxes_transaction()
                if tax_transaction is not None:
                    valid_transactions.append(tax_transaction)
                    valid_transactions.sort(key=lambda x: x.priority)
        for transaction in valid_transactions:
            # if "Sepp" in transaction.name:
            #     print("debug")
            #logger.debug(f"Executing transaction {transaction.name} on {current_date}")
            try:
                actions = transaction.execute(days, current_date)
            except NotAllowedNegativeBalance:
                logger.error(f"Failed on transaction: {transaction.name}")
                raise
            for action in actions:
                # TODO: consider: https://github.com/dfurtado/dataclass-csv
                action_log_data = action.dict()
                action_log_data["date"] = current_date
                self._actions_to_write.append(action_log_data)
                if self.fed_tax_handler is not None:
                    self.fed_tax_handler.process_action(action, current_date)
    
    def save_state(self, date: date):
        for asset in self.assets:
            data = asset.log.model_dump()
            data["date"] = date
            self._asset_log.writerow(data)
        self.log()

    def log(self):
        self._action_log.writerows(self._actions_to_write)
        self._actions_to_write = []
    
    def close_log(self):
        self.log()
        if self.fed_tax_handler is not None:
            self.fed_tax_handler.close()
        self._action_log_file.close()

    def _build_asset_map(self):
        self._asset_map = {a.name: a for a in self.assets}

    def load_dates(self, *args, **kwargs):
        for transaction in self.transactions:
            transaction.load_dates(*args, **kwargs)

    def load_interest_rates(self, *args, **kwargs):
        for transaction in self.transactions:
            transaction.load_interest_rate(*args, **kwargs)
        if self.fed_tax_handler is not None:
            self.fed_tax_handler.load_interest_rate(*args, **kwargs)

class ActionManagerInput(BaseModel):
    assets: Optional[List[Union[asset_input_options, Path]]] = []
    transactions: Optional[List[Union[transaction_input_options, Path]]] = []
    fed_tax_handler: Optional[FederalTaxInput] = None
    
    def load_paths(self, **kwargs):
        self.transactions = load_list_path(
            self.transactions,
            transaction_input_options,
            **kwargs,
        )
        self.assets = load_list_path(
            self.assets,
            asset_input_options,
            **kwargs,
        )

    def to_dc_model(self):
        if self.fed_tax_handler is not None:
            fed_tax_handler=self.fed_tax_handler.to_dc_model()
        else:
            fed_tax_handler=None
        return ActionManager(
            transactions=[t.to_dc_model() for t in self.transactions],
            assets=[a.to_dc_model() for a in self.assets],
            fed_tax_handler=fed_tax_handler,
        )
    
    @field_serializer('assets')
    def serialize_assets(self, assets: list):
        new_assets = []
        for asset in assets:
            new_value = asset
            if type(asset) == Path:
                new_value = str(asset)
            else:
                new_value = asset.model_dump()
            new_assets.append(new_value)
        return new_assets

if __name__ == "__main__":
    am = ActionManager()
    am = ActionManager(assets=["a.yml"])
    print("here")