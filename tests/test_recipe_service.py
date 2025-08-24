import json
from pathlib import Path
import pytest
from datetime import datetime, timedelta
from meal_time.models.recipe import Recipe
from meal_time.services.recipe_service import RecipeService


@pytest.fixture
def sample_recipe():
    return {
        "name": "Test Recipe",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "steps": ["Chop vegetables", "Cook for 10 minutes"],
        "prep_time": 10,
        "cook_time": 15,
        "total_time": 25,
        "step_times": [5, 10]  # Added step times
    }


@pytest.fixture
def sample_recipe_no_times():
    """Recipe without step times for testing generation"""
    return {
        "name": "No Times Recipe",
        "ingredients": ["Test ingredient"],
        "steps": ["Prep ingredients", "Bake in oven"],
        "prep_time": 5,
        "cook_time": 20,
        "total_time": 25,
        "step_times": []  # Empty step times
    }


@pytest.fixture
def multiple_recipes():
    return [
        {
            "name": "Quick Salad",
            "ingredients": ["Lettuce", "Tomatoes", "Dressing"],
            "steps": ["Wash lettuce", "Chop tomatoes", "Mix with dressing"],
            "prep_time": 10,
            "cook_time": 0,
            "total_time": 10,
            "step_times": [3, 4, 3]
        },
        {
            "name": "Pasta Dish",
            "ingredients": ["Pasta", "Sauce", "Cheese"],
            "steps": ["Boil water", "Cook pasta", "Add sauce", "Serve with cheese"],
            "prep_time": 5,
            "cook_time": 15,
            "total_time": 20,
            "step_times": [2, 12, 3, 3]
        }
    ]


@pytest.fixture
def temp_recipes_file(tmp_path, sample_recipe):
    file = tmp_path / "recipes.json"
    file.write_text(json.dumps([sample_recipe]))
    return file


@pytest.fixture
def temp_multiple_recipes_file(tmp_path, multiple_recipes):
    file = tmp_path / "recipes.json"
    file.write_text(json.dumps(multiple_recipes))
    return file


# Original tests (updated)
def test_load_recipes(temp_recipes_file, sample_recipe):
    service = RecipeService(storage_path=temp_recipes_file)
    recipes = service.list_recipes()

    assert len(recipes) == 1
    assert recipes[0].name == sample_recipe["name"]
    assert recipes[0].prep_time == sample_recipe["prep_time"]
    assert recipes[0].cook_time == sample_recipe["cook_time"]
    assert recipes[0].total_time == sample_recipe["total_time"]
    assert recipes[0].steps == sample_recipe["steps"]
    assert recipes[0].step_times == sample_recipe["step_times"]


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

    # Test case insensitive search
    recipe_case = service.get_recipe_by_name("test recipe")
    assert recipe_case is not None

    missing = service.get_recipe_by_name("Nonexistent")
    assert missing is None


# NEW TESTS for scheduling functionality

def test_generate_missing_step_times(tmp_path, sample_recipe_no_times):
    """Test that missing step times are generated"""
    file = tmp_path / "recipes.json"
    file.write_text(json.dumps([sample_recipe_no_times]))

    service = RecipeService(storage_path=file)
    recipe = service.get_recipe_by_name("No Times Recipe")

    # Initially no step times
    assert len(recipe.step_times) == 0

    # Generate step times
    service.generate_missing_step_times()

    # Now should have step times
    updated_recipe = service.get_recipe_by_name("No Times Recipe")
    assert len(updated_recipe.step_times) == len(updated_recipe.steps)
    assert all(time > 0 for time in updated_recipe.step_times)


def test_organize_single_recipe(temp_recipes_file):
    """Test organizing a single recipe"""
    service = RecipeService(storage_path=temp_recipes_file)
    target_time = datetime.now() + timedelta(hours=1)

    steps = service.organize_recipes(["Test Recipe"], target_time)

    assert len(steps) == 2  # Two steps in sample recipe
    assert all("recipe_name" in step for step in steps)
    assert all("text" in step for step in steps)
    assert all("duration" in step for step in steps)
    assert all("start_time" in step for step in steps)
    assert all("end_time" in step for step in steps)

    # Check timing logic - steps should be in chronological order
    assert steps[0]["start_time"] <= steps[1]["start_time"]

    # Last step should end at target time
    assert steps[-1]["end_time"] == target_time


def test_organize_multiple_recipes(temp_multiple_recipes_file):
    """Test organizing multiple recipes together"""
    service = RecipeService(storage_path=temp_multiple_recipes_file)
    target_time = datetime.now() + timedelta(hours=1)

    steps = service.organize_recipes(["Quick Salad", "Pasta Dish"], target_time)

    # Should have steps from both recipes
    salad_steps = [s for s in steps if s["recipe_name"] == "Quick Salad"]
    pasta_steps = [s for s in steps if s["recipe_name"] == "Pasta Dish"]

    assert len(salad_steps) == 3  # Quick Salad has 3 steps
    assert len(pasta_steps) == 4  # Pasta Dish has 4 steps

    # Steps should be sorted by start time
    for i in range(1, len(steps)):
        assert steps[i - 1]["start_time"] <= steps[i]["start_time"]

    # Both recipes should finish at target time
    salad_end = max(s["end_time"] for s in salad_steps)
    pasta_end = max(s["end_time"] for s in pasta_steps)
    assert salad_end == target_time
    assert pasta_end == target_time


def test_step_classification(temp_multiple_recipes_file):
    """Test that steps are correctly classified"""
    service = RecipeService(storage_path=temp_multiple_recipes_file)
    target_time = datetime.now() + timedelta(hours=1)

    steps = service.organize_recipes(["Quick Salad", "Pasta Dish"], target_time)

    # Check that classification fields exist
    for step in steps:
        assert "is_prep" in step
        assert "is_cooking" in step
        assert "can_multitask" in step
        assert isinstance(step["is_prep"], bool)
        assert isinstance(step["is_cooking"], bool)
        assert isinstance(step["can_multitask"], bool)

    # Find specific steps and check classification
    chop_step = next((s for s in steps if "chop" in s["text"].lower()), None)
    if chop_step:
        assert chop_step["is_prep"] == True

    cook_step = next((s for s in steps if "cook" in s["text"].lower()), None)
    if cook_step:
        assert cook_step["is_cooking"] == True


def test_cooking_summary(temp_multiple_recipes_file):
    """Test cooking summary generation"""
    service = RecipeService(storage_path=temp_multiple_recipes_file)
    target_time = datetime.now() + timedelta(hours=1)

    summary = service.get_cooking_summary(["Quick Salad", "Pasta Dish"], target_time)

    # Check summary structure
    assert "total_time" in summary
    assert "start_time" in summary
    assert "end_time" in summary
    assert "recipes" in summary
    assert "total_steps" in summary
    assert "prep_steps" in summary
    assert "cooking_steps" in summary

    # Check values make sense
    assert summary["total_time"] > 0
    assert summary["start_time"] < target_time
    assert summary["end_time"] == target_time
    assert summary["recipes"] == ["Quick Salad", "Pasta Dish"]
    assert summary["total_steps"] == 7  # 3 + 4 steps


def test_export_cooking_timeline(temp_multiple_recipes_file):
    """Test timeline export functionality"""
    service = RecipeService(storage_path=temp_multiple_recipes_file)
    target_time = datetime.now() + timedelta(hours=1)

    export_text = service.export_cooking_timeline(["Quick Salad", "Pasta Dish"], target_time)

    # Check export contains expected content
    assert "MEAL TIME COOKING PLAN" in export_text
    assert "Target Completion:" in export_text
    assert "Start Cooking At:" in export_text
    assert "Quick Salad" in export_text
    assert "Pasta Dish" in export_text

    # Should contain time stamps
    assert ":" in export_text  # Time format HH:MM


def test_empty_recipe_list():
    """Test handling of empty recipe list"""
    service = RecipeService(storage_path="nonexistent.json")
    target_time = datetime.now() + timedelta(hours=1)

    steps = service.organize_recipes([], target_time)
    assert steps == []

    summary = service.get_cooking_summary([], target_time)
    assert summary["total_time"] == 0


def test_nonexistent_recipe():
    """Test handling of nonexistent recipes"""
    service = RecipeService(storage_path="nonexistent.json")
    target_time = datetime.now() + timedelta(hours=1)

    steps = service.organize_recipes(["Fake Recipe"], target_time)
    assert steps == []


def test_recipe_with_mismatched_step_times(tmp_path):
    """Test handling of recipes with mismatched steps and step_times"""
    mismatched_recipe = {
        "name": "Mismatched Recipe",
        "ingredients": ["Ingredient 1"],
        "steps": ["Step 1", "Step 2", "Step 3"],  # 3 steps
        "step_times": [5, 10]  # Only 2 times
    }

    file = tmp_path / "recipes.json"
    file.write_text(json.dumps([mismatched_recipe]))

    service = RecipeService(storage_path=file)
    service.generate_missing_step_times()

    recipe = service.get_recipe_by_name("Mismatched Recipe")
    assert len(recipe.step_times) == len(recipe.steps)


# Integration test with actual data (if it exists)
def test_load_recipes_from_data_folder():
    """Test loading from actual data folder"""
    data_file = Path(__file__).parent.parent / "data" / "recipes.json"

    if not data_file.exists():
        pytest.skip("No data/recipes.json file found")

    service = RecipeService(storage_path=str(data_file))
    recipes = service.list_recipes()

    # Basic checks
    assert len(recipes) > 0, "No recipes loaded from data folder"
    assert all(isinstance(r, Recipe) for r in recipes), "Loaded items are not Recipe instances"

    # Check first recipe has expected fields
    first = recipes[0]
    assert hasattr(first, "name")
    assert hasattr(first, "ingredients")
    assert hasattr(first, "steps")

    # Test organizing with real data
    if len(recipes) >= 2:
        recipe_names = [r.name for r in recipes[:2]]
        target_time = datetime.now() + timedelta(hours=1)

        steps = service.organize_recipes(recipe_names, target_time)
        assert len(steps) > 0

        summary = service.get_cooking_summary(recipe_names, target_time)
        assert summary["total_time"] > 0


# Performance test
def test_organize_many_recipes(tmp_path):
    """Test organizing many recipes doesn't crash"""
    many_recipes = []
    for i in range(10):
        many_recipes.append({
            "name": f"Recipe {i}",
            "ingredients": [f"Ingredient {j}" for j in range(3)],
            "steps": [f"Step {j}" for j in range(5)],
            "step_times": [5, 10, 15, 8, 12],
            "prep_time": 10,
            "cook_time": 30,
            "total_time": 40
        })

    file = tmp_path / "recipes.json"
    file.write_text(json.dumps(many_recipes))

    service = RecipeService(storage_path=file)
    recipe_names = [f"Recipe {i}" for i in range(10)]
    target_time = datetime.now() + timedelta(hours=2)

    # This should complete without errors
    steps = service.organize_recipes(recipe_names, target_time)
    assert len(steps) == 50  # 10 recipes * 5 steps each

    summary = service.get_cooking_summary(recipe_names, target_time)
    assert summary["total_steps"] == 50