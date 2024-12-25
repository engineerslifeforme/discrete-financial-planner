from pathlib import Path
from datetime import date
import math

import pandas as pd
import yaml
from pydantic import BaseModel

from planner.transactions import transaction_options

IMPORTANT_COLUMNS = [
    "Amount",
    "Type",
    "Source",
    "Destination",
    "Growth",
    "Date",
    "Federal Tax Payment",
    "State Tax Deductible",
    "Fed Tax Deductible",
    "Start",
    "Stop",
    "Ignore",
    "Priority",
]

def main(workbook_path: Path):
    assert(workbook_path.exists())
    book = pd.ExcelFile(workbook_path)
    transactions = []
    for sheet_name in book.sheet_names:
        transactions.extend(get_expenses(workbook_path, sheet_name))
    dumped_transactions = [t.model_dump() for t in transactions]
    Path("transactions.yml").write_text(yaml.safe_dump(dumped_transactions))
    print("here")

def get_expenses(workbook_path: Path, sheet_name: str):
    data = pd.read_excel(
        workbook_path,
        sheet_name
    )
    header_row_index = get_header_row_index(data)
    if header_row_index is None:
        return []
    else:
        return extract_expenses(
            workbook_path,
            sheet_name,
            header_row_index,
        )

def cbool(value: float) -> bool:
    return value != 0.0

def cdate(value) -> date:
    try:
        return value.date()
    except AttributeError:
        pass
    try:
        isnan = math.isnan(value)
    except TypeError:
        isnan = False
    
    if isnan:
        return None
    elif type(value) == str:
        return value
    else:
        print("here")

def cstr(value) -> str:
    if type(value) != str:
        return None
    else:
        return value
    
def extract_expenses(workbook_path: Path, sheet_name: str, header_row_index: int):
    data = pd.read_excel(
        workbook_path,
        sheet_name,
        skiprows=header_row_index+1,
    )
    expenses = []
    class UnknownTransaction(BaseModel):
        transaction: transaction_options
    for entry in data.loc[~data["Ignore"].isna(), :].to_dict(orient="records"):
        if cbool(entry["Ignore"]):
            continue
        expenses.append(UnknownTransaction(transaction={
            "name":entry["Name"],
            "start":cdate(entry["Start"]),
            "end":cdate(entry["Stop"]),
            "base_amount":entry["Amount"],
            "source_name":cstr(entry["Source"]),
            "destination_name":cstr(entry["Destination"]),
            "interest_rate":entry["Growth"],
            "priority":entry["Priority"],
            "frequency":entry["Type"],
            "first_date": cdate(entry["Date"]),
        }).transaction)
    return expenses

def get_header_row_index(data: pd.DataFrame) -> int:
    tdata = data.transpose()
    header_row_index = None
    for index, column in enumerate(tdata.columns):
        good_column = True
        for column_name in IMPORTANT_COLUMNS:
            try:
                good_column = good_column and any(tdata[column].str.contains(column_name).fillna(False))
                if not good_column:
                    break
            except AttributeError:
                good_column = False
                break
        if good_column:
            header_row_index = index
            break
    return header_row_index


if __name__ == "__main__":
    workbook_path = Path("converter/202410_expenses.xlsx")
    main(workbook_path)