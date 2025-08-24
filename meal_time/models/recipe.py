from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Recipe:
    name: str
    ingredients: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    prep_time: Optional[int] = None   # in minutes
    cook_time: Optional[int] = None   # in minutes
    total_time: Optional[int] = None  # in minutes
    step_times: List[int] = field(default_factory=list)  # per-step duration in minutes

    def __str__(self):
        return self.name
