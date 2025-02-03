from datetime import date
from decimal import Decimal
from dataclasses import dataclass

from pydantic import BaseModel

from planner.transactions import Transaction

@dataclass
class ActionLog:
    date: date
    action_type: str
    amount: Decimal
    changed_item: str
    transaction: Transaction

    def to_dict(self) -> dict:
        dict_data = self.transaction.to_dict()
        dict_data.update({
            "date": self.date,
            "action_type": self.action_type,
            "amount": self.amount,
            "changed_item": self.changed_item,
        })
        return dict_data