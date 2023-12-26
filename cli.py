import argparse
import datetime
from dateutil.relativedelta import relativedelta 
from pathlib import Path

import yaml
import pandas as pd

from planner import Simulation

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--start_date",
        help="Start Date of Simulation (Default today)",
        type=valid_date,
        default=None
    )
    parser.add_argument(
        "-e",
        "--end_date",
        help="End Date of Simulation (default 20 years)",
        type=valid_date,
        default=None
    )
    parser.add_argument(
        "config_file_path",
        help="Path to planner YAML configuration file",
        type=Path,
    )
    args = parser.parse_args()
    assert(args.config_file_path.exists()), f"Could not find {args.config_file_path}"
    main(args.config_file_path, args.start_date, args.end_date)

def main(configuration_path: Path, start: datetime.date = None, end: datetime.date = None):
    configuration = yaml.safe_load(configuration_path.read_text())
    if start is None:
        start = datetime.datetime.today().date()
    else:
        configuration["start"] = start
    if end is None:
        end = datetime.datetime.today().date() + relativedelta(years=20)
    else:
        configuration["end"] = end
    simulation = Simulation(**configuration)
    _, asset_states = simulation.run()
    pd.DataFrame(asset_states).to_csv("output.csv", index=False)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    cli()