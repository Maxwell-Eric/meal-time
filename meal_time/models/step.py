# meal_time/models/step.py
from typing import Optional

class Step:
    def __init__(self, text: str, estimated_time: Optional[int] = None):
        self.text = text
        self.estimated_time = estimated_time
