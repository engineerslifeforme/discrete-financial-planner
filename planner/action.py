from datetime import date
from typing import Optional

from pydantic import BaseModel

class Action(BaseModel):
    description: str
    amount: float = 0.0
    priority: int = 200
    source_name: Optional[str] = None
    destination_name: Optional[str] = None
    empty_source: bool = False
