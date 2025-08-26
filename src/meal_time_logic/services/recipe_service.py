import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from src.meal_time_logic.models.recipe import Recipe
from src.meal_time_logic.services.step_time_parser_service import process_recipe_steps
from src.meal_time_logic.ml.step_time_predictor import StepTimePredictor
from src.meal_time_logic.services.timeline_service import TimelineService
from src.meal_time_logic.services.validation_service import ValidationService
from src.meal_time_logic.services.web_scraper_service import WebScraperService
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

        # Ensure the directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.recipes = self._load()

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
            changed_recipes = []
            for recipe in self.recipes:
                if not recipe.step_times or len(recipe.step_times) != len(recipe.steps):
                    print(f"Generating step times for: {recipe.name}")
                    recipe.step_times = [self.predictor.predict(step) for step in recipe.steps]
                    changed_recipes.append(recipe.name)

            if changed_recipes:
                self._save()
                print(f"Updated {len(changed_recipes)} recipes with predicted step times")
                return {"updated_count": len(changed_recipes), "updated_recipes": changed_recipes}
            else:
                return {"updated_count": 0, "updated_recipes": []}

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

    def process_recipe_step_times(self, recipe: Recipe) -> Recipe:
        """
        Process a recipe to extract/predict step times using the new parser.
        Returns a new recipe with updated steps and step_times.
        """

        if not recipe.steps:
            return recipe

        # Process steps to extract times
        expanded_steps, step_times, confidence_info = process_recipe_steps(recipe.steps)

        # Create updated recipe
        updated_recipe = Recipe(
            name=recipe.name,
            ingredients=recipe.ingredients,
            steps=expanded_steps,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            total_time=recipe.total_time,
            step_times=step_times
        )

        # Update total time if not set
        if not updated_recipe.total_time and step_times:
            updated_recipe.total_time = sum(step_times)

        # Store confidence information (you might want to add this to Recipe model)
        # For now, we'll just use it internally

        return updated_recipe

    def enhance_all_recipe_times(self):
        """
        Re-process all recipes to improve step time detection.
        This will find times in step text and split multi-time steps.
        """
        try:
            enhanced_count = 0
            for i, recipe in enumerate(self.recipes):
                print(f"Processing recipe {i + 1}/{len(self.recipes)}: {recipe.name}")

                original_step_count = len(recipe.steps)
                enhanced_recipe = self.process_recipe_step_times(recipe)

                # Only update if we made improvements
                if (len(enhanced_recipe.steps) != original_step_count or
                        enhanced_recipe.step_times != recipe.step_times):
                    self.recipes[i] = enhanced_recipe
                    enhanced_count += 1
                    print(f"  Enhanced: {original_step_count} -> {len(enhanced_recipe.steps)} steps")

            if enhanced_count > 0:
                self._save()
                print(f"Enhanced {enhanced_count} recipes with better step timing")
            else:
                print("All recipes already have good step timing")

        except Exception as e:
            raise StepTimePredictionException(f"Failed to enhance recipe times: {e}")

    def add_recipe_with_time_processing(self, recipe: Recipe):
        """
        Add a recipe with automatic step time processing.
        This will parse times from step text and predict missing times.
        """
        # Process step times first
        processed_recipe = self.process_recipe_step_times(recipe)

        # Then use the normal add process with validation
        self.add_recipe(processed_recipe)

        return processed_recipe

    def update_recipe_with_time_processing(self, recipe: Recipe):
        """
        Update a recipe with automatic step time processing.
        """
        # Process step times first
        processed_recipe = self.process_recipe_step_times(recipe)

        # Then use the normal update process
        self.update_recipe(processed_recipe)

        return processed_recipe

    def get_step_time_analysis(self, recipe: Recipe) -> Dict:
        """
        Analyze a recipe's step times and return detailed information.
        """

        # Process the steps
        expanded_steps, step_times, confidence_info = process_recipe_steps(recipe.steps)

        # Calculate statistics
        total_time = sum(step_times)
        extracted_count = sum(1 for c in confidence_info if c == 'extracted')
        predicted_count = sum(1 for c in confidence_info if c == 'predicted')

        # Find steps that might need attention
        needs_review = []
        for i, (step, time_val, conf) in enumerate(zip(expanded_steps, step_times, confidence_info)):
            if conf == 'predicted' and time_val == 5:  # Default prediction
                needs_review.append({
                    'step_number': i + 1,
                    'text': step,
                    'reason': 'Using default prediction - may need manual review'
                })
            elif 'until' in step.lower() and conf == 'predicted':
                needs_review.append({
                    'step_number': i + 1,
                    'text': step,
                    'reason': 'Vague timing ("until done") - consider specifying time'
                })

        return {
            'original_steps': len(recipe.steps),
            'processed_steps': len(expanded_steps),
            'total_time_minutes': total_time,
            'extracted_times': extracted_count,
            'predicted_times': predicted_count,
            'confidence_breakdown': {
                'extracted': extracted_count,
                'predicted': predicted_count,
                'user_set': sum(1 for c in confidence_info if c == 'user_set')
            },
            'needs_review': needs_review,
            'expanded_steps': expanded_steps,
            'step_times': step_times,
            'confidence_info': confidence_info
        }
