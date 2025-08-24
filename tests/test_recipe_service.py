import json
from pathlib import Path
import pytest
from meal_time.models.recipe import Recipe
from meal_time.services.recipe_service import RecipeService


@pytest.fixture
def sample_recipe():
    return {
        "name": "Test Recipe",
        "prep_time": 10,
        "cook_time": 15,
        "total_time": 25,
        "steps": ["Step 1", "Step 2"]
    }


@pytest.fixture
def temp_recipes_file(tmp_path, sample_recipe):
    file = tmp_path / "recipes.json"
    file.write_text(json.dumps([sample_recipe]))
    return file


def test_load_recipes(temp_recipes_file, sample_recipe):
    service = RecipeService(storage_path=temp_recipes_file)
    recipes = service.list_recipes()

    assert len(recipes) == 1
    assert recipes[0].name == sample_recipe["name"]
    assert recipes[0].prep_time == sample_recipe["prep_time"]
    assert recipes[0].cook_time == sample_recipe["cook_time"]
    assert recipes[0].total_time == sample_recipe["total_time"]
    assert recipes[0].steps == sample_recipe["steps"]


def test_add_recipe(tmp_path, sample_recipe):
    file = tmp_path / "recipes.json"
    service = RecipeService(storage_path=file)
    new_recipe = Recipe(**sample_recipe)
    service.add_recipe(new_recipe)

    loaded = service.list_recipes()
    assert len(loaded) == 1
    assert loaded[0].name == "Test Recipe"


def test_get_recipe_by_name(temp_recipes_file, sample_recipe):
    service = RecipeService(storage_path=temp_recipes_file)
    recipe = service.get_recipe_by_name("Test Recipe")
    assert recipe is not None
    assert recipe.name == sample_recipe["name"]

    missing = service.get_recipe_by_name("Nonexistent")
    assert missing is None


def test_organize_recipes(temp_recipes_file):
    service = RecipeService(storage_path=temp_recipes_file)
    steps = service.organize_recipes(["Test Recipe"])
    assert steps == [("Test Recipe", "Step 1"), ("Test Recipe", "Step 2")]


def test_load_recipes_from_data_folder():
    # Assume your JSON is located at MealTIme/data/recipes.json
    data_file = Path(__file__).parent.parent / "data" / "recipes.json"

    service = RecipeService(storage_path=str(data_file))

    recipes = service.list_recipes()

    # Basic checks
    assert len(recipes) > 0, "No recipes loaded from data folder"
    assert all(isinstance(r, Recipe) for r in recipes), "Loaded items are not Recipe instances"

    # Optional: check first recipe has expected fields
    first = recipes[0]
    assert hasattr(first, "name")
    assert hasattr(first, "ingredients")
    assert hasattr(first, "steps")
    assert recipes[0].name == "ABC"

    for r in recipes:
        print(r.name)
