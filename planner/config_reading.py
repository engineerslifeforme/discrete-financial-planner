from pathlib import Path
from dateutil.relativedelta import relativedelta
import datetime

import yaml

def combine_configs(config_list: list) -> dict:
    """ Combines multiple potentially subset dicts to a single

    :param config_list: multiple subset dictionaries
    :type config_list: list
    :return: single combined dictionary of data
    :rtype: dict
    """
    simple_keys = ["start", "end"]
    list_keys = [
        "transactions",
        "mortgages",
        "interest_rates",
        "assets",
    ]
    skeleton = {k: [] for k in list_keys}
    skeleton["dates"] = {}
    for s in simple_keys:
        skeleton[s] = None
    for c in config_list:
        try:
            skeleton["federal_income_taxes"] = c["federal_income_taxes"]
        except KeyError:
            pass
        try:
            skeleton["state_income_taxes"] = c["state_income_taxes"]
        except KeyError:
            pass
        try:
            skeleton["dates"].update(c["dates"])
        except KeyError:
            pass
        for s in simple_keys:
            try:
                skeleton[s] = c[s]
            except KeyError:
                pass
        for l in list_keys:
            try:
                skeleton[l].extend(c[l])
            except KeyError:
                pass
    return skeleton

def read_configuration(configuration_paths: list, list_path: Path, start: datetime.date = None, end: datetime.date = None):
    if list_path is not None:
        configuration_paths = [list_path.parent / p for p in yaml.safe_load(list_path.read_text())]
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
    return configuration