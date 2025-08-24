from dataclasses import dataclass
from typing import List
from meal_time.models.recipe import Recipe


@dataclass
class MealPlan:
    name: str
    recipes: List[Recipe]
