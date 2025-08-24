# meal_time/services/validation_service.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from meal_time.models.recipe import Recipe
from exceptions import *
from config import Config


class ValidationService:
    """Service for validating inputs and business logic"""

    def __init__(self):
        self.config = Config()

    def validate_recipe(self, recipe: Recipe) -> List[str]:
        """Validate a recipe and return list of issues"""
        issues = []

        if not recipe.name or not recipe.name.strip():
            issues.append("Recipe name is required")

        if not recipe.steps:
            issues.append("Recipe must have at least one step")

        if not recipe.ingredients:
            issues.append("Recipe must have at least one ingredient")

        if recipe.step_times:
            if len(recipe.step_times) != len(recipe.steps):
                issues.append("Number of step times must match number of steps")

            if any(time < self.config.MIN_STEP_TIME for time in recipe.step_times):
                issues.append(f"Step times must be at least {self.config.MIN_STEP_TIME} minute(s)")

            if any(time > self.config.MAX_STEP_TIME for time in recipe.step_times):
                issues.append(f"Step times must be less than {self.config.MAX_STEP_TIME} minutes")

        # Validate time consistency
        if recipe.prep_time and recipe.prep_time < 0:
            issues.append("Prep time cannot be negative")

        if recipe.cook_time and recipe.cook_time < 0:
            issues.append("Cook time cannot be negative")

        return issues

    def validate_target_time(self, target_time: datetime, current_time: datetime = None) -> Dict:
        """Validate target cooking time"""
        if current_time is None:
            current_time = datetime.now()

        result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }

        # Check if target time is in the past
        if target_time <= current_time:
            result["valid"] = False
            result["errors"].append("Target time must be in the future")
            return result

        # Check if target time is too close
        time_diff = (target_time - current_time).total_seconds() / 60  # minutes
        if time_diff < self.config.MIN_PREP_TIME:
            result["warnings"].append(f"Very tight timing! Less than {self.config.MIN_PREP_TIME} minutes available")

        # Check if target time is unreasonably far
        if time_diff > 24 * 60:  # More than 24 hours
            result["warnings"].append("Target time is more than 24 hours away")

        return result

    def validate_recipe_selection(self, recipe_names: List[str], all_recipes: List[Recipe]) -> Dict:
        """Validate recipe selection for timeline generation"""
        result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "valid_recipes": [],
            "invalid_recipes": []
        }

        if not recipe_names:
            result["valid"] = False
            result["errors"].append("At least one recipe must be selected")
            return result

        recipe_dict = {r.name: r for r in all_recipes}

        for name in recipe_names:
            if name not in recipe_dict:
                result["invalid_recipes"].append(name)
                result["errors"].append(f"Recipe '{name}' not found")
                continue

            recipe = recipe_dict[name]
            recipe_issues = self.validate_recipe(recipe)

            if recipe_issues:
                result["invalid_recipes"].append(name)
                result["errors"].extend([f"{name}: {issue}" for issue in recipe_issues])
            else:
                result["valid_recipes"].append(recipe)

        if not result["valid_recipes"]:
            result["valid"] = False
            result["errors"].append("No valid recipes selected")

        return result

    def estimate_total_time_needed(self, recipes: List[Recipe]) -> int:
        """Estimate total time needed for recipes (conservative estimate)"""
        max_total_time = 0
        for recipe in recipes:
            if recipe.total_time:
                max_total_time = max(max_total_time, recipe.total_time)
            elif recipe.prep_time and recipe.cook_time:
                total = recipe.prep_time + recipe.cook_time
                max_total_time = max(max_total_time, total)
            elif recipe.step_times:
                total = sum(recipe.step_times)
                max_total_time = max(max_total_time, total)

        return max_total_time

    def validate_timeline_feasibility(self, recipes: List[Recipe], target_time: datetime,
                                      current_time: datetime = None) -> Dict:
        """Validate if timeline is feasible given time constraints"""
        if current_time is None:
            current_time = datetime.now()

        result = {
            "feasible": True,
            "warnings": [],
            "errors": [],
            "time_needed": 0,
            "time_available": 0
        }

        time_available = (target_time - current_time).total_seconds() / 60
        time_needed = self.estimate_total_time_needed(recipes)

        result["time_available"] = int(time_available)
        result["time_needed"] = time_needed

        if time_needed > time_available:
            shortage = time_needed - time_available
            result["feasible"] = False
            result["errors"].append(f"Need {shortage:.0f} more minutes to complete all recipes")
        elif time_needed > time_available * self.config.WARNING_THRESHOLD:
            result["warnings"].append("Timeline will be very tight - consider starting some prep early")

        return result
