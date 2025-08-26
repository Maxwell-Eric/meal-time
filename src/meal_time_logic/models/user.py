from dataclasses import dataclass
from typing import List
from src.meal_time_logic.models.meal_plan import MealPlan


@dataclass
class User:
    username: str
    meal_plans: List[MealPlan]
