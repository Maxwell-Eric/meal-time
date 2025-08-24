# meal_time/config.py
from pathlib import Path


class Config:
    # File paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"

    # Try to find recipes.json in multiple locations
    POTENTIAL_RECIPE_PATHS = [
        DATA_DIR / "recipes.json",  # data/recipes.json (production)
        PROJECT_ROOT / "recipes.json",  # recipes.json (development)
        Path.cwd() / "recipes.json",  # Current working directory
        Path.cwd() / "data" / "recipes.json"  # CWD/data/recipes.json
    ]

    # Find the first existing path, or default to data/recipes.json
    RECIPES_FILE = None
    for path in POTENTIAL_RECIPE_PATHS:
        if path.exists():
            RECIPES_FILE = path
            break

    if RECIPES_FILE is None:
        RECIPES_FILE = DATA_DIR / "recipes.json"  # Default fallback

    ML_MODEL_FILE = PROJECT_ROOT / "ml_step_time_model.pkl"

    # UI Settings
    DEFAULT_TARGET_TIME = "18:00"  # 6 PM
    PAGE_TITLE = "Meal Time 🍴"
    RECIPES_PER_PAGE = 10

    # Recipe Colors for UI
    RECIPE_COLORS = ["🔴", "🟡", "🟢", "🔵", "🟣", "🟠", "⚫", "⚪"]

    # Step Classification Keywords
    PREP_KEYWORDS = ['chop', 'dice', 'slice', 'mince', 'prep', 'cut', 'wash', 'peel', 'measure']
    COOKING_KEYWORDS = ['cook', 'bake', 'fry', 'boil', 'simmer', 'sauté', 'roast', 'grill', 'heat']
    MULTITASK_KEYWORDS = ['bake', 'simmer', 'marinate', 'chill', 'rest', 'rise', 'cool']

    # ML Settings
    DEFAULT_STEP_TIME = 5  # minutes
    MIN_STEP_TIME = 1  # minutes
    MAX_STEP_TIME = 180  # 3 hours

    # Timing Validation
    MIN_PREP_TIME = 10  # minimum minutes needed for any meal
    WARNING_THRESHOLD = 0.8  # warn if less than 80% of estimated time available
