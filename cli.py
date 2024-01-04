import argparse
import datetime
from dateutil.relativedelta import relativedelta 
from pathlib import Path
from decimal import Decimal

import yaml
import pandas as pd

from planner import Simulation, combine_configs
from planner.common import round

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
        "-c",
        "--config_file_path",
        action='append',
        help="Path to planner YAML configuration file",
        type=Path,
        default=[]
    )
    parser.add_argument(
        "-l",
        "--yaml_path_list",
        help="YAML file with list of YAML file paths",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    assert(args.yaml_path_list is not None or len(args.config_file_path) > 0), "You must provide either one or more config files via -c or file with a list via -l"
    for c_path in args.config_file_path:
        assert(c_path.exists()), f"Could not find {c_path}"
    if args.yaml_path_list is not None:
        assert(args.yaml_path_list.exists()), f"Provided list file path does not exists: {args.yaml_path_list}"
    main(args.config_file_path, args.yaml_path_list, args.start_date, args.end_date)

def main(configuration_paths: list, list_path: Path, start: datetime.date = None, end: datetime.date = None):
    if list_path is not None:
        configuration_paths = [Path(p) for p in yaml.safe_load(list_path.read_text())]
    configurations = [
        yaml.safe_load(p.read_text()) for p in configuration_paths
    ]
    configuration = combine_configs(configurations)
    if start is None:
        start = datetime.datetime.today().date()
    else:
        configuration["start"] = start
    if end is None:
        end = datetime.datetime.today().date() + relativedelta(years=20)
    else:
        configuration["end"] = end
    simulation = Simulation(**configuration)
    _, asset_states, action_logs, tax_data, state_tax_data = simulation.run()
    pd.DataFrame(asset_states).to_csv("output.csv", index=False)
    pd.DataFrame(action_logs).to_csv("changes.csv", index=False)
    if tax_data is not None:
        pd.DataFrame(tax_data).to_csv("yearly_fed_taxes.csv", index=False)
    if state_tax_data is not None:
        pd.DataFrame(state_tax_data).to_csv("yearly_state_taxes.csv", index=False)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    cli()