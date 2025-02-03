import json
from pathlib import Path

import pandas as pd
import calendar

from planner.util import interest_of_x

def main():
    data = pd.read_csv("datahub_io.csv", parse_dates=["Date"])
    data = data.sort_values(by="Date")
    data["value_pct_change"] = data["SP500"].pct_change()
    data["cpi_pct_change"] = data["Consumer Price Index"].pct_change()
    data = data.dropna()
    data["year"] = data["Date"].dt.year
    data["month"] = data["Date"].dt.month
    interest_and_inflation = []
    for entry in data.to_dict("records"):
        days_in_month = calendar.monthrange(entry["year"], entry["month"])[1]
        interest_and_inflation.append({
            "year": entry["year"],
            "month": entry["month"],
            "value_pct_change": entry["value_pct_change"],
            "value_pct_change_day": interest_of_x(entry["value_pct_change"], days_in_month),
            "cpi_pct_change": entry["cpi_pct_change"],
            "cpi_pct_change_day": interest_of_x(entry["cpi_pct_change"], days_in_month),
        })
    Path("planner/interest_rates/interest_and_inflation.py").write_text(f"INTEREST_AND_INFLATION = {json.dumps(interest_and_inflation)}")
    print("done")

if __name__ == "__main__":
    main()