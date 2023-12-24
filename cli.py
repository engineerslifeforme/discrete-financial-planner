import argparse
import datetime
from dateutil.relativedelta import relativedelta 

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--start_date",
        help="Start Date of Simulation (Default today)",
        type=valid_date,
        default=datetime.datetime.today().date
    )
    parser.add_argument(
        "-e",
        "--end_date",
        help="End Date of Simulation (default 20 years)",
        type=valid_date,
        default=datetime.datetime.today().date + relativedelta(years=20)
    )

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    cli()