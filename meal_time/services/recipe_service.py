import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from meal_time.models.recipe import Recipe
from meal_time.ml.step_time_predictor import StepTimePredictor
from meal_time.services.timeline_service import TimelineService
from meal_time.services.validation_service import ValidationService
from meal_time.services.web_scraper_service import WebScraperService
from exceptions import *
from config import Config


class RecipeService:
    def __init__(self, storage_path: str = None):
        self.config = Config()

        # Use provided path or fall back to config
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = self.config.RECIPES_FILE

        print(f"Loading recipes from: {self.storage_path.absolute()}")

        # Ensure the directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.recipes = self._load()
        print(f"Loaded {len(self.recipes)} recipes")

        self.predictor = StepTimePredictor()
        self.timeline_service = TimelineService()
        self.validation_service = ValidationService()
        self.web_scraper = WebScraperService()

    def _load(self) -> List[Recipe]:
        """Load recipes from storage"""
        if not self.storage_path.exists():
            print(f"Recipe file not found at {self.storage_path.absolute()}")
            print("Creating empty recipe list")
            return []

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print("Recipe file is empty")
                    return []

                data = json.loads(content)
                print(f"Found {len(data)} recipes in file")
                recipes = []

                for i, recipe_data in enumerate(data):
                    try:
                        recipe = Recipe(**recipe_data)
                        recipes.append(recipe)
                    except Exception as e:
                        print(f"Error loading recipe {i}: {e}")
                        continue

                return recipes

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            raise InvalidRecipeException("recipes.json", f"Invalid JSON format: {e}")
        except Exception as e:
            print(f"Error loading recipes: {e}")
            return []

    def _save(self):
        """Save recipes to storage"""
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([r.__dict__ for r in self.recipes], f, indent=4)

    def add_recipe(self, recipe: Recipe):
        """Add a new recipe with validation"""
        # Validate recipe before adding
        issues = self.validation_service.validate_recipe(recipe)
        if issues:
            raise InvalidRecipeException(recipe.name, "; ".join(issues))

        # Check for duplicate names
        if self.get_recipe_by_name(recipe.name):
            raise InvalidRecipeException(recipe.name, "Recipe with this name already exists")

        self.recipes.append(recipe)
        self._save()

    def update_recipe(self, recipe: Recipe):
        """Update an existing recipe"""
        # Validate recipe
        issues = self.validation_service.validate_recipe(recipe)
        if issues:
            raise InvalidRecipeException(recipe.name, "; ".join(issues))

        # Find and replace existing recipe
        for i, existing in enumerate(self.recipes):
            if existing.name.lower() == recipe.name.lower():
                self.recipes[i] = recipe
                self._save()
                return

        raise RecipeNotFoundException(recipe.name)

    def delete_recipe(self, name: str):
        """Delete a recipe by name"""
        for i, recipe in enumerate(self.recipes):
            if recipe.name.lower() == name.lower():
                del self.recipes[i]
                self._save()
                return

        raise RecipeNotFoundException(name)

    def list_recipes(self) -> List[Recipe]:
        """Get all recipes"""
        return self.recipes

    def get_recipe_by_name(self, name: str) -> Optional[Recipe]:
        """Get a recipe by name (case-insensitive)"""
        for r in self.recipes:
            if r.name.lower() == name.lower():
                return r
        return None

    def generate_missing_step_times(self):
        """Use ML predictor to fill missing step times"""
        try:
            changed = False
            for recipe in self.recipes:
                if not recipe.step_times or len(recipe.step_times) != len(recipe.steps):
                    print(f"Generating step times for: {recipe.name}")
                    recipe.step_times = [self.predictor.predict(step) for step in recipe.steps]
                    changed = True

            if changed:
                self._save()
                print("Updated recipes with predicted step times")
        except Exception as e:
            raise StepTimePredictionException(f"Failed to generate step times: {e}")

    def organize_recipes(self, names: List[str], target_time: datetime = None) -> List[Dict]:
        """
        Organize recipe steps to finish all dishes simultaneously.
        Returns timeline steps as dictionaries for UI compatibility.
        """
        if not target_time:
            target_time = datetime.now() + timedelta(hours=1)

        # Validate inputs
        validation_result = self.validation_service.validate_recipe_selection(names, self.recipes)
        if not validation_result["valid"]:
            raise InvalidRecipeException("selection", "; ".join(validation_result["errors"]))

        # Validate target time
        time_validation = self.validation_service.validate_target_time(target_time)
        if not time_validation["valid"]:
            raise ImpossibleTimingException("; ".join(time_validation["errors"]))

        # Get valid recipes
        recipes = validation_result["valid_recipes"]

        # Ensure all recipes have step times
        self.generate_missing_step_times()

        # Reload recipes to get updated step times
        updated_recipes = []
        for recipe in recipes:
            updated_recipe = self.get_recipe_by_name(recipe.name)
            if updated_recipe:
                updated_recipes.append(updated_recipe)

        # Check feasibility
        feasibility = self.validation_service.validate_timeline_feasibility(updated_recipes, target_time)
        if not feasibility["feasible"]:
            required_start = target_time - timedelta(minutes=feasibility["time_needed"])
            raise ImpossibleTimingException(
                "; ".join(feasibility["errors"]),
                required_start_time=required_start
            )

        # Generate timeline using TimelineService
        try:
            timeline_steps = self.timeline_service.generate_timeline(updated_recipes, target_time)

            # Validate the generated timeline
            timeline_validation = self.timeline_service.validate_timeline(timeline_steps, datetime.now())
            if not timeline_validation["valid"]:
                error_issues = [issue["message"] for issue in timeline_validation["issues"] if
                                issue["severity"] == "error"]
                if error_issues:
                    raise ImpossibleTimingException("; ".join(error_issues))

            # Convert TimelineStep objects to dictionaries for UI compatibility
            return [self._timeline_step_to_dict(step) for step in timeline_steps]

        except Exception as e:
            if isinstance(e, MealTimeException):
                raise
            else:
                raise TimelineException(f"Failed to generate timeline: {e}")

    def _timeline_step_to_dict(self, step) -> Dict:
        """Convert TimelineStep to dictionary for backward compatibility with UI"""
        return {
            "text": step.text,
            "duration": step.duration,
            "start_time": step.start_time,
            "end_time": step.end_time,
            "recipe_name": step.recipe_name,
            "step_number": step.step_number,
            "recipe_color": step.recipe_color,
            "is_prep": step.is_prep,
            "is_cooking": step.is_cooking,
            "can_multitask": step.can_multitask,
            "order": step.order,
            "time_gap": step.time_gap
        }

    def get_cooking_summary(self, names: List[str], target_time: datetime = None) -> Dict:
        """Get a summary of the cooking plan using TimelineService"""
        if not target_time:
            target_time = datetime.now() + timedelta(hours=1)

        try:
            # Get valid recipes
            validation_result = self.validation_service.validate_recipe_selection(names, self.recipes)
            if not validation_result["valid"]:
                return self._empty_summary()

            recipes = validation_result["valid_recipes"]

            # Generate timeline and get summary
            timeline_steps = self.timeline_service.generate_timeline(recipes, target_time)
            summary = self.timeline_service.get_timeline_summary(timeline_steps, target_time)

            return summary

        except Exception:
            return self._empty_summary()

    def _empty_summary(self) -> Dict:
        """Return empty summary when no valid recipes"""
        return {
            "total_time": 0,
            "start_time": None,
            "end_time": None,
            "recipes": [],
            "total_steps": 0,
            "prep_steps": 0,
            "cooking_steps": 0,
            "multitask_opportunities": 0
        }

    def export_cooking_timeline(self, names: List[str], target_time: datetime = None) -> str:
        """Export timeline as formatted text"""
        if not target_time:
            target_time = datetime.now() + timedelta(hours=1)

        try:
            steps = self.organize_recipes(names, target_time)
            summary = self.get_cooking_summary(names, target_time)

            output = []
            output.append("🍽️  MEAL TIME COOKING PLAN")
            output.append("═" * 50)
            output.append(f"Target Completion: {target_time.strftime('%Y-%m-%d at %H:%M')}")

            if summary['start_time']:
                output.append(f"Start Cooking At: {summary['start_time'].strftime('%H:%M')}")
                output.append(f"Total Time: {summary['total_time']} minutes")

            output.append(f"Recipes: {', '.join(names)}")
            output.append("")

            current_time = None
            for step in steps:
                step_time = step["start_time"].strftime("%H:%M")
                if step_time != current_time:
                    output.append(f"\n⏰ {step_time}")
                    current_time = step_time

                multitask = " (Can multitask)" if step["can_multitask"] else ""
                output.append(
                    f"  {step['recipe_color']} [{step['recipe_name']}] {step['text']} ({step['duration']} min){multitask}")

            return "\n".join(output)

        except MealTimeException as e:
            return f"❌ Error generating timeline: {str(e)}"

    def get_recipe_validation_issues(self, recipe_name: str) -> List[str]:
        """Get validation issues for a specific recipe"""
        recipe = self.get_recipe_by_name(recipe_name)
        if not recipe:
            return ["Recipe not found"]

        return self.validation_service.validate_recipe(recipe)

    def import_recipe_from_url(self, url: str) -> Dict:
        """Import a recipe from a web URL"""
        try:
            # Check if URL can be scraped
            if not self.web_scraper.can_scrape_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL format",
                }

            # Scrape the recipe
            recipe = self.web_scraper.scrape_recipe(url)

            # Validate the scraped recipe
            issues = self.validation_service.validate_recipe(recipe)

            # Check for duplicate names and modify if needed
            original_name = recipe.name
            counter = 1
            while self.get_recipe_by_name(recipe.name):
                recipe.name = f"{original_name} ({counter})"
                counter += 1

            # Add the recipe
            self.recipes.append(recipe)
            self._save()

            return {
                "success": True,
                "recipe": recipe,
                "validation_issues": issues,
                "name_changed": recipe.name != original_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def preview_recipe_from_url(self, url: str) -> Dict:
        """Preview a recipe from URL without saving it"""
        try:
            # Check if URL can be scraped
            if not self.web_scraper.can_scrape_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL format"
                }

            # Scrape the recipe
            recipe = self.web_scraper.scrape_recipe(url)

            # Validate the recipe
            issues = self.validation_service.validate_recipe(recipe)

            return {
                "success": True,
                "recipe": recipe,
                "validation_issues": issues
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
