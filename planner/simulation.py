from datetime import date

from pydantic import BaseModel

class Simulation(BaseModel):
    start: date
    end: date