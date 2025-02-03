import sys
from pathlib import Path
from decimal import Decimal
from typing import Union

import pandas as pd
import yaml
from pydantic import BaseModel

from planner.assets.asset import AssetInput
from planner.assets.debt import DebtInput
from planner.action_manager import ActionManager
from planner.util import ZERO

NEGATIVE_ONE = Decimal("-1")

# TODO: Generature maturity transactions

def main(networth_csv_path: Path):    
    assert(networth_csv_path.exists())
    data = pd.read_csv(networth_csv_path, skiprows=20)
    export(data)
    print("here")

def clean_decimal(decimal_str: str) -> Decimal:
    if "-" in decimal_str:
        return ZERO
    else:
        return Decimal(decimal_str.replace("$", "").replace(",", ""))

def export(data: pd.DataFrame):

    class AssetReader(BaseModel):
        data: Union[AssetInput, DebtInput]

    final_assets = []
    for asset in data.to_dict(orient="records"):
        a_type = asset["Type"]
        a_category = asset["Category"].lower()
        balance = clean_decimal(asset["Balance"])
        if a_category == "debt":
            balance = balance * NEGATIVE_ONE
        if a_type == "Temporary":
            continue
        final_assets.append(AssetReader(data={
            "name":asset["Name"],
            "starting_balance": balance,
            "type":a_category,
            "category":a_type,
        }))
    dumped_assets = [a.data.model_dump() for a in final_assets]
    Path("assets.yml").write_text(yaml.safe_dump(dumped_assets))

if __name__ == "__main__":
    #networth_csv_path = Path(sys.argv[1])
    networth_csv_path = Path("converter/networth.csv")
    main(networth_csv_path)