

from meal_time.models.recipe import Recipe
from meal_time.ml.step_time_predictor import StepTimePredictor
from recipe_scrapers import scrape_me  # assuming you are using this library


class ScraperService:

    def __init__(self):
        self.predictor = StepTimePredictor()

    def scrape_recipe(self, url: str) -> Recipe:
        """
        Scrape a recipe from a URL and generate step times automatically.
        Returns a Recipe object with steps and predicted step_times.
        """
        scraper = scrape_me(url)

        recipe = Recipe(
            name=scraper.title(),
            ingredients=scraper.ingredients(),
            steps=scraper.instructions().split("\n"),
            prep_time=scraper.prep_time(),
            cook_time=scraper.cook_time(),
            total_time=scraper.total_time(),
            step_times=[]
        )

        # Generate step_times if missing or count mismatch
        if not recipe.step_times or len(recipe.step_times) != len(recipe.steps):
            recipe.step_times = [self.predictor.predict(s) for s in recipe.steps]

        return recipe
