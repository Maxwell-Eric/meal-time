# src/meal_time_logic/services/recipe_filter_service.py
from typing import List, Dict, Any
from src.meal_time_logic.models.recipe import Recipe


class RecipeFilterService:
    """Service for filtering and sorting recipes based on various criteria"""

    def filter_recipes(self, recipes: List[Recipe], criteria: Dict[str, Any]) -> List[Recipe]:
        """Filter and sort recipes based on the given criteria"""
        filtered = recipes.copy()

        # Apply search filter
        filtered = self._apply_search_filter(filtered, criteria.get('search', ''))

        # Apply timing completeness filter
        filtered = self._apply_timing_filter(filtered, criteria.get('timing_filter', 'All'))

        # Apply sorting
        filtered = self._apply_sorting(filtered, criteria.get('sort_by', 'Recent'))

        return filtered

    def _apply_search_filter(self, recipes: List[Recipe], search_term: str) -> List[Recipe]:
        """Filter recipes by search term in name, ingredients, or steps"""
        if not search_term:
            return recipes

        search_lower = search_term.lower()
        return [recipe for recipe in recipes if self._matches_search(recipe, search_lower)]

    def _matches_search(self, recipe: Recipe, search_term: str) -> bool:
        """Check if recipe matches the search term"""
        # Search in recipe name
        if search_term in recipe.name.lower():
            return True

        # Search in ingredients
        if any(search_term in ingredient.lower() for ingredient in recipe.ingredients):
            return True

        # Search in steps
        if any(search_term in step.lower() for step in recipe.steps):
            return True

        return False

    def _apply_timing_filter(self, recipes: List[Recipe], timing_filter: str) -> List[Recipe]:
        """Filter recipes by timing completeness"""
        if timing_filter == "Complete":
            return [r for r in recipes if self._has_complete_timing(r)]
        elif timing_filter == "Incomplete":
            return [r for r in recipes if not self._has_complete_timing(r)]
        else:  # "All"
            return recipes

    def _has_complete_timing(self, recipe: Recipe) -> bool:
        """Check if recipe has complete step timing"""
        return (recipe.step_times and
                len(recipe.step_times) == len(recipe.steps))

    def _apply_sorting(self, recipes: List[Recipe], sort_by: str) -> List[Recipe]:
        """Sort recipes based on the specified criteria"""
        if sort_by == "Name":
            return sorted(recipes, key=lambda r: r.name.lower())
        elif sort_by == "Steps":
            return sorted(recipes, key=lambda r: len(r.steps), reverse=True)
        elif sort_by == "Time":
            return sorted(recipes, key=self._get_total_time, reverse=True)
        else:  # "Recent" - keep original order (most recently added first)
            return recipes

    def _get_total_time(self, recipe: Recipe) -> int:
        """Get total time for sorting purposes"""
        if recipe.step_times:
            return sum(recipe.step_times)
        elif recipe.total_time:
            return recipe.total_time
        else:
            return 0


class RecipeSearchCriteria:
    """Data class for recipe search criteria"""

    def __init__(
            self,
            search: str = "",
            timing_filter: str = "All",
            sort_by: str = "Recent"
    ):
        self.search = search
        self.timing_filter = timing_filter
        self.sort_by = sort_by

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for service consumption"""
        return {
            'search': self.search,
            'timing_filter': self.timing_filter,
            'sort_by': self.sort_by
        }
    