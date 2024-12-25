from decimal import Decimal
import math
from typing import List
from pathlib import Path

from pydantic import BaseModel
import yaml

ZERO = Decimal("0.00")

def future_value(present_value: float, interest: float, periods: int) -> float:
    """ Future value calculation

    :param present_value: present day value
    :type present_value: float
    :param interest: rate per period
    :type interest: float
    :param periods: number of periods
    :type periods: int
    :return: future value
    :rtype: float

    https://www.realized1031.com/glossary/future-value-fv#:~:text=In%20its%20most%20basic%20form,the%20number%20of%20time%20periods.
    """
    return present_value*math.pow((1+interest), periods)

def load_list_path(input_list: list, desired_types, root: Path = "."):
    class PathList(BaseModel):
        list: List[desired_types]

    new_list = []
    for item in input_list:
        if isinstance(item, Path):
            new_list.extend(PathList(list=yaml.safe_load((root / item).read_text())).list)
        else:
            new_list.append(item)
    return new_list