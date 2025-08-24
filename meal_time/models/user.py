from dataclasses import dataclass
from typing import List
from meal_time.models.meal_plan import MealPlan


@dataclass
class User:
    username: str
    meal_plans: List[MealPlan]
