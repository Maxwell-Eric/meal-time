import pytest
from unittest.mock import Mock, patch
from meal_time.services.web_scraper_service import WebScraperService
from meal_time.models.recipe import Recipe


class TestWebScraperServiceIntegration:
    """Test integration of StepSplitter with WebScraperService"""
    
    @patch('meal_time.services.web_scraper_service.scrape_me')
    def test_scrape_recipe_with_step_splitting(self, mock_scrape_me):
        """Test that scraped recipes have their steps split correctly"""
        # Mock the scraper response
        mock_scraper = Mock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.ingredients.return_value = ["Ingredient 1", "Ingredient 2"]
        mock_scraper.instructions.return_value = [
            "Chop vegetables",
            "Simmer for 10 minutes, then bake for 25 minutes",
            "Let cool for 5 minutes and serve"
        ]
        mock_scraper.prep_time.return_value = 15
        mock_scraper.cook_time.return_value = 40
        mock_scraper.total_time.return_value = 55
        
        mock_scrape_me.return_value = mock_scraper
        
        # Test the service
        service = WebScraperService()
        recipe = service.scrape_recipe("http://example.com/recipe")
        
        # Verify basic recipe properties
        assert recipe.name == "Test Recipe"
        assert len(recipe.ingredients) == 2
        assert recipe.prep_time == 15
        assert recipe.cook_time == 40
        assert recipe.total_time == 55
        
        # Verify step splitting occurred
        assert len(recipe.steps) > 3  # Should be more than original 3 due to splitting
        assert len(recipe.steps) == len(recipe.step_times)
        
        # Check that the multi-time step was split
        step_text = " ".join(recipe.steps).lower()
        assert "simmer" in step_text
        assert "bake" in step_text
        
        # Verify times were extracted
        assert any(time == 10 for time in recipe.step_times)  # Simmer time
        assert any(time == 25 for time in recipe.step_times)  # Bake time
        assert any(time == 5 for time in recipe.step_times)   # Cool time
    
    @patch('meal_time.services.web_scraper_service.scrape_me')
    def test_scrape_recipe_with_complex_steps(self, mock_scrape_me):
        """Test complex step splitting scenarios"""
        mock_scraper = Mock()
        mock_scraper.title.return_value = "Complex Recipe"
        mock_scraper.ingredients.return_value = ["Ingredient"]
        mock_scraper.instructions.return_value = [
            "Heat oil for 2 minutes, then add onions and cook for 5 minutes, then add garlic and cook for 1 minute",
            "Pour in broth and simmer for 20 minutes. Season to taste and serve immediately.",
        ]
        mock_scraper.prep_time.return_value = None
        mock_scraper.cook_time.return_value = None  
        mock_scraper.total_time.return_value = None
        
        mock_scrape_me.return_value = mock_scraper
        
        service = WebScraperService()
        recipe = service.scrape_recipe("http://example.com/complex-recipe")
        
        # Should have more steps than the original 2
        assert len(recipe.steps) > 2
        
        # Should have extracted multiple times
        extracted_times = [time for time in recipe.step_times if time in [1, 2, 5, 20]]
        assert len(extracted_times) >= 2  # At least some times should be extracted
    
    @patch('meal_time.services.web_scraper_service.scrape_me')
    def test_scrape_recipe_no_splitting_needed(self, mock_scrape_me):
        """Test recipes that don't need step splitting"""
        mock_scraper = Mock()
        mock_scraper.title.return_value = "Simple Recipe"
        mock_scraper.ingredients.return_value = ["Ingredient"]
        mock_scraper.instructions.return_value = [
            "Preheat oven to 350°F",
            "Mix ingredients in bowl",
            "Bake for 30 minutes"
        ]
        mock_scraper.prep_time.return_value = 10
        mock_scraper.cook_time.return_value = 30
        mock_scraper.total_time.return_value = 40
        
        mock_scrape_me.return_value = mock_scraper
        
        service = WebScraperService()
        recipe = service.scrape_recipe("http://example.com/simple-recipe")
        
        # Should have same number of steps (no splitting needed)
        assert len(recipe.steps) == 3
        assert len(recipe.step_times) == 3
        
        # Should have extracted the bake time
        assert 30 in recipe.step_times
    
    @patch('meal_time.services.web_scraper_service.scrape_me')
    def test_scrape_recipe_string_instructions(self, mock_scrape_me):
        """Test handling of string format instructions"""
        mock_scraper = Mock()
        mock_scraper.title.return_value = "String Recipe"
        mock_scraper.ingredients.return_value = ["Ingredient"]
        # Instructions as a single string with newlines
        mock_scraper.instructions.return_value = "Chop vegetables\nSimmer for 10 minutes, then bake for 25 minutes\nServe hot"
        mock_scraper.prep_time.return_value = 10
        mock_scraper.cook_time.return_value = 35
        mock_scraper.total_time.return_value = 45
        
        mock_scrape_me.return_value = mock_scraper
        
        service = WebScraperService()
        recipe = service.scrape_recipe("http://example.com/string-recipe")
        
        # Should handle string format and split correctly
        assert len(recipe.steps) > 3  # Should be split
        assert len(recipe.steps) == len(recipe.step_times)
        
        # Check for expected content
        step_text = " ".join(recipe.steps).lower()
        assert "chop" in step_text
        assert "simmer" in step_text
        assert "bake" in step_text
        assert "serve" in step_text


class TestStepSplitterRealWorldExamples:
    """Test step splitter with realistic recipe examples"""
    
    def test_split_recipe_steps_real_examples(self):
        """Test with real-world recipe step examples"""
        from meal_time.utils.step_splitter import StepSplitter
        
        original_steps = [
            "Preheat oven to 375°F and line a baking sheet with parchment paper",
            "In a large bowl, combine flour, sugar, and salt. Add cold butter and mix for 2 minutes until crumbly, then add egg and vanilla and mix for 1 minute more",
            "Roll out dough and cut into shapes. Bake for 12-15 minutes until golden brown",
            "Cool on rack for 10 minutes, then transfer to serving plate and dust with powdered sugar"
        ]
        
        new_steps, new_step_times = StepSplitter.split_recipe_steps(original_steps)
        
        # Should have more steps than original
        assert len(new_steps) > len(original_steps)
        assert len(new_steps) == len(new_step_times)
        
        # Check that specific times were extracted
        assert 2 in new_step_times   # Mix for 2 minutes
        assert 1 in new_step_times   # Mix for 1 minute more
        assert 10 in new_step_times  # Cool for 10 minutes
        
        # Check for time ranges (should be averaged)
        range_times = [time for time in new_step_times if time in [12, 13, 14, 15]]
        assert len(range_times) > 0  # Should have extracted something from 12-15 minutes
        
    def test_split_pasta_recipe(self):
        """Test with a typical pasta recipe"""
        from meal_time.utils.step_splitter import StepSplitter
        
        original_steps = [
            "Bring a large pot of salted water to boil for 5 minutes",
            "Add pasta and cook for 8-10 minutes until al dente, then drain and reserve 1 cup pasta water",
            "Meanwhile, heat olive oil in large skillet for 1 minute, add garlic and cook for 30 seconds until fragrant",
            "Add pasta to skillet with sauce and toss for 2 minutes, adding pasta water as needed"
        ]
        
        new_steps, new_step_times = StepSplitter.split_recipe_steps(original_steps)
        
        # Verify extraction of key times
        assert 5 in new_step_times    # Boil for 5 minutes  
        assert 1 in new_step_times    # Heat oil for 1 minute
        assert 2 in new_step_times    # Toss for 2 minutes
        
        # Check for range average (8-10 minutes should be ~9)
        pasta_cook_times = [time for time in new_step_times if time in [8, 9, 10]]
        assert len(pasta_cook_times) > 0
        
        # Should have split the complex step with "meanwhile"
        step_text = " ".join(new_steps).lower()
        assert "meanwhile" in step_text or "heat olive oil" in step_text
        assert "add garlic" in step_text