import sys
from pathlib import Path
from decimal import Decimal

import pandas as pd
import yaml

from planner.assets.asset import Asset
from planner.assets.debt import Debt
from planner.action_manager import ActionManager
from planner.util import ZERO

NEGATIVE_ONE = Decimal("-1")

# TODO: Generature maturity transactions

def main(networth_csv_path: Path):    
    assert(networth_csv_path.exists())
    assets = get_assets(networth_csv_path)
    debts = get_debts(networth_csv_path)
    export(assets, debts)
    print("here")

def clean_decimal(decimal_str: str) -> Decimal:
    if "-" in decimal_str:
        return ZERO
    else:
        return Decimal(decimal_str.replace("$", "").replace(",", ""))

def export(assets: pd.DataFrame, debts: pd.DataFrame):
    final_assets = []
    for asset in assets.to_dict(orient="records"):
        final_assets.append(Asset(
            name=asset["name"],
            starting_balance=clean_decimal(asset["balance"]),
            type="asset"
        ))
    for debt in debts.to_dict(orient="records"):
        final_assets.append(Debt(
            name=debt["name"],
            starting_balance=clean_decimal(debt["balance"]) * NEGATIVE_ONE,
            type="debt"
        ))
    dumped_assets = [a.model_dump() for a in final_assets]
    Path("assets.yml").write_text(yaml.safe_dump(dumped_assets))
    

def get_debts(networth_csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        networth_csv_path, 
        skiprows=22, 
        header = 0,
        names = [
            "dnc_a",
            "dnc_b",
            "dnc_c",
            "name",
            "balance",
            "dnc_d",
            "dnc_e",
            "dnc_f",
            "dnc_g",
            "dnc_h",
            "dnc_i",
            "dnc_j",
            "dnc_k",
        ]
    )
    df = df.iloc[:2, :][["name", "balance"]].dropna()
    return df

def get_assets(networth_csv_path) -> pd.DataFrame:
    df = pd.read_csv(
        networth_csv_path, 
        skiprows=9, 
        header = 0,
        names = [
            "investment_name",
            "dnc_a",
            "dnc_b",
            "dnc_c",
            "investment_balance",
            "dnc_d",
            "physical_name",
            "physical_balance",
            "dnc_e",
            "cash_name",
            "cash_balance",
            "dnc_f",
            "dnc_g",
        ]
    )
    df = df.iloc[:10, :]
    investments = df[["investment_name", "investment_balance"]]
    physical = df[["physical_name", "physical_balance"]]
    cash = df[["cash_name", "cash_balance"]]
    items_to_concat = []
    for data in [investments, physical, cash]:
        data.columns = ["name", "balance"]
        items_to_concat.append(data)
    df = pd.concat(items_to_concat).dropna()
    return df

if __name__ == "__main__":
    #networth_csv_path = Path(sys.argv[1])
    networth_csv_path = Path("converter/networth.csv")
    main(networth_csv_path)