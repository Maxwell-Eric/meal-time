# meal_time/services/web_scraper_service.py
from meal_time.models.recipe import Recipe
from meal_time.ml.step_time_predictor import StepTimePredictor
from meal_time.utils.step_splitter import StepSplitter
try:
    from recipe_scrapers import scrape_me
except ImportError:
    # Fallback if recipe-scrapers is not installed
    def scrape_me(url):
        raise ImportError("recipe-scrapers library not installed. Run: pip install recipe-scrapers")

from exceptions import *


class WebScraperService:
    """Service for scraping recipes from web URLs using recipe-scrapers library"""

    def __init__(self):
        self.predictor = StepTimePredictor()

    def can_scrape_url(self, url: str) -> bool:
        """Check if URL can potentially be scraped"""
        try:
            # Basic URL validation
            if not url or not url.startswith(('http://', 'https://')):
                return False
            return True
        except:
            return False

    def scrape_recipe(self, url: str) -> Recipe:
        """
        Scrape a recipe from a URL and generate step times automatically.
        Returns a Recipe object with steps and predicted step_times.
        """
        try:
            scraper = scrape_me(url)

            # Extract instructions and handle different formats
            instructions = scraper.instructions()
            if isinstance(instructions, str):
                # Split by newlines and filter empty lines
                steps = [step.strip() for step in instructions.split("\n") if step.strip()]
            elif isinstance(instructions, list):
                steps = [str(step).strip() for step in instructions if str(step).strip()]
            else:
                steps = [str(instructions)]

            # Split steps with multiple time instructions
            split_steps, split_step_times = StepSplitter.split_recipe_steps(steps)

            try:
                prep_time = scraper.prep_time()
            except Exception:
                prep_time = None

            try:
                cook_time = scraper.cook_time()
            except Exception:
                cook_time = None

            try:
                total_time = scraper.total_time()
            except Exception:
                total_time = None

            recipe = Recipe(
                name=scraper.title() or "Scraped Recipe",
                ingredients=scraper.ingredients() or [],
                steps=split_steps,
                prep_time=prep_time,
                cook_time=cook_time,
                total_time=total_time,
                step_times=split_step_times
            )

            # Generate step_times if missing or count mismatch
            if not recipe.step_times or len(recipe.step_times) != len(recipe.steps):
                recipe.step_times = [self.predictor.predict(s) for s in recipe.steps]

            return recipe

        except Exception as e:
            raise InvalidRecipeException(url, f"Failed to scrape recipe: {str(e)}")
