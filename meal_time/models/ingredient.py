from dataclasses import dataclass


@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str
