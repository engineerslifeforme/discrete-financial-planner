from decimal import Decimal
import math
from typing import List
from pathlib import Path
from datetime import timedelta

from pydantic import BaseModel
import yaml

ZERO = Decimal("0.00")
NEGATIVE_ONE = Decimal("-1")
ONE_DAY = timedelta(days=1)

def interest_of_x(interest: float, periods_in_x: int) -> float:
    """ Convert interest rates

    :param interest: current rate
    :type interest: float
    :param periods_in_x: periods in current period
    :type periods_in_x: int
    :return: new rate
    :rtype: float

    daily_rate = interest_of_x(yearly_rate, 365)
    """
    return math.pow(1+interest, 1/periods_in_x) - 1

def get_compounded_rate(principal: float, future_value: float, periods: int) -> float:
    return math.pow(future_value / principal, 1/periods) - 1.0

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

def future_interest(present_value: float, interest: float, periods: int) -> float:
    """ Future value calculation

    :param present_value: present day value
    :type present_value: float
    :param interest: rate per period
    :type interest: float
    :param periods: number of periods
    :type periods: int
    :return: future value
    :rtype: float

    Modified version of future value for interest only
    """
    return future_value(present_value, interest, periods) - present_value

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