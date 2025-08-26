from dataclasses import dataclass
from typing import List
from src.meal_time_logic.models.recipe import Recipe


@dataclass
class MealPlan:
    name: str
    recipes: List[Recipe]
