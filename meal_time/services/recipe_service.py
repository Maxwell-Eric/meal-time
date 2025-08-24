import json
from pathlib import Path
from typing import Optional

from meal_time.models.recipe import Recipe

class RecipeService:
  def __init__(self, storage_path: str = "data/recipes.json"):
    self.storage_path = Path(storage_path)
    self.recipes = self._load()

  def _load(self) -> list[Recipe]:
    if self.storage_path.exists():
      try:
        with open(self.storage_path, "r", encoding="utf-8") as f:
          content = f.read().strip()
          if not content:
            return []
          data = json.loads(content)
          return [Recipe(**r) for r in data]
      except json.JSONDecodeError:
        return []
    return []

  def _save(self):
    with open(self.storage_path, "w", encoding="utf-8") as f:
      json.dump([r.__dict__ for r in self.recipes], f, indent=4)

  def add_recipe(self, recipe: Recipe):
    self.recipes.append(recipe)
    self._save()

  def list_recipes(self) -> list[Recipe]:
    return self.recipes

  def get_recipe_by_name(self, name: str) -> Optional[Recipe]:
    for r in self.recipes:
      if r.name.lower() == name.lower():
        return r
    return None

  def organize_recipes(self, names: list[str]) -> list[dict]:
    """
    Returns a list of steps with:
    - text: step description
    - estimated_time: optional
    - recipe_name: name of recipe
    """
    organized = []
    for name in names:
      recipe = self.get_recipe_by_name(name)
      if recipe:
        for step in recipe.steps:
          organized.append({
            "text": step,
            "estimated_time": None,  # placeholder
            "recipe_name": recipe.name
          })
    return organized
