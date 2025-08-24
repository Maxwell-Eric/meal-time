import pytest
from meal_time.utils.step_splitter import StepSplitter, SplitStep


class TestStepSplitter:
    """Test cases for the StepSplitter utility"""
    
    def test_extract_time_from_text_minutes(self):
        """Test extracting time in minutes"""
        # Basic minute patterns
        assert StepSplitter.extract_time_from_text("Cook for 10 minutes") == (10, "10 minutes")
        assert StepSplitter.extract_time_from_text("Simmer for 25 mins") == (25, "25 mins")
        assert StepSplitter.extract_time_from_text("Bake 15 min") == (15, "15 min")
        
        # With decimals
        assert StepSplitter.extract_time_from_text("Rest for 2.5 minutes") == (2, "2.5 minutes")
        
        # No time found
        assert StepSplitter.extract_time_from_text("Chop the vegetables") == (None, None)
    
    def test_extract_time_from_text_hours(self):
        """Test extracting time in hours"""
        # Hour patterns
        assert StepSplitter.extract_time_from_text("Bake for 1 hour") == (60, "1 hour")
        assert StepSplitter.extract_time_from_text("Marinate for 2 hours") == (120, "2 hours")
        assert StepSplitter.extract_time_from_text("Cook 1.5 hrs") == (90, "1.5 hrs")
        
        # Hours and minutes
        assert StepSplitter.extract_time_from_text("Bake for 1 hour and 30 minutes") == (90, "1 hour and 30 minutes")
        assert StepSplitter.extract_time_from_text("Cook 2 hrs 15 mins") == (135, "2 hrs 15 mins")
    
    def test_extract_time_from_text_ranges(self):
        """Test extracting time ranges"""
        assert StepSplitter.extract_time_from_text("Cook for 10-15 minutes") == (12, "10-15 minutes")  # Average
        assert StepSplitter.extract_time_from_text("Bake 1-2 hours") == (90, "1-2 hours")  # Average in minutes
    
    def test_extract_time_from_text_approximate(self):
        """Test extracting approximate times"""
        assert StepSplitter.extract_time_from_text("Cook for about 20 minutes") == (20, "about 20 minutes")
        assert StepSplitter.extract_time_from_text("Simmer around 1 hour") == (60, "around 1 hour")
    
    def test_has_multiple_time_instructions_single_time(self):
        """Test detection with single time instruction"""
        assert not StepSplitter.has_multiple_time_instructions("Cook for 10 minutes")
        assert not StepSplitter.has_multiple_time_instructions("Bake for 1 hour")
        assert not StepSplitter.has_multiple_time_instructions("Chop vegetables")
    
    def test_has_multiple_time_instructions_multiple_times(self):
        """Test detection with multiple time instructions"""
        assert StepSplitter.has_multiple_time_instructions("Simmer for 10 minutes, then bake for 25 minutes")
        assert StepSplitter.has_multiple_time_instructions("Cook 15 minutes and then rest 5 minutes")
        assert StepSplitter.has_multiple_time_instructions("Bake for 30 minutes. Cool for 10 minutes")
    
    def test_has_multiple_time_instructions_conjunctions(self):
        """Test detection with conjunctions (even single time)"""
        assert StepSplitter.has_multiple_time_instructions("Cook for 10 minutes, then remove from heat")
        assert StepSplitter.has_multiple_time_instructions("Bake for 25 minutes and serve immediately")
        assert StepSplitter.has_multiple_time_instructions("Simmer for 15 minutes. Season to taste")
    
    def test_split_step_no_splitting_needed(self):
        """Test steps that don't need splitting"""
        result = StepSplitter.split_step("Cook for 10 minutes")
        assert len(result) == 1
        assert result[0].instruction == "Cook for 10 minutes"
        assert result[0].time_minutes == 10
        
        result = StepSplitter.split_step("Chop the vegetables")
        assert len(result) == 1
        assert result[0].instruction == "Chop the vegetables"
        assert result[0].time_minutes is None
    
    def test_split_step_basic_splitting(self):
        """Test basic step splitting with conjunctions"""
        result = StepSplitter.split_step("Simmer for 10 minutes, then bake for 25 minutes")
        assert len(result) == 2
        
        # First step
        assert "simmer" in result[0].instruction.lower()
        assert result[0].time_minutes == 10
        
        # Second step  
        assert "bake" in result[1].instruction.lower()
        assert result[1].time_minutes == 25
    
    def test_split_step_then_conjunction(self):
        """Test splitting with 'then' conjunction"""
        result = StepSplitter.split_step("Cook pasta for 12 minutes, then drain and add sauce")
        assert len(result) == 2
        
        assert "cook pasta" in result[0].instruction.lower()
        assert result[0].time_minutes == 12
        
        assert "drain and add sauce" in result[1].instruction.lower()
    
    def test_split_step_period_separation(self):
        """Test splitting with period separation"""
        result = StepSplitter.split_step("Bake for 30 minutes. Cool for 10 minutes before serving.")
        assert len(result) == 2
        
        assert "bake" in result[0].instruction.lower()
        assert result[0].time_minutes == 30
        
        assert "cool" in result[1].instruction.lower()
        assert result[1].time_minutes == 10
    
    def test_split_step_complex_example(self):
        """Test complex splitting scenario"""
        text = "Heat oil for 2 minutes, then add onions and cook for 5 minutes, then add garlic and cook for 1 minute"
        result = StepSplitter.split_step(text)
        
        # Should create multiple steps
        assert len(result) >= 2
        
        # Check that times are extracted
        times = [step.time_minutes for step in result if step.time_minutes is not None]
        assert len(times) >= 2
        assert 2 in times or 5 in times or 1 in times
    
    def test_split_step_text_cleaning(self):
        """Test that split step text is properly cleaned"""
        result = StepSplitter.split_step("cook for 10 minutes, then bake for 25 minutes")
        
        # Should have proper capitalization
        assert result[0].instruction[0].isupper()
        assert result[1].instruction[0].isupper()
        
        # Should end with periods
        for step in result:
            if not step.instruction.endswith(('!', '?')):
                assert step.instruction.endswith('.')
    
    def test_split_recipe_steps_integration(self):
        """Test the full recipe steps splitting function"""
        original_steps = [
            "Chop vegetables",
            "Simmer for 10 minutes, then bake for 25 minutes", 
            "Cook pasta for 12 minutes. Drain and serve.",
            "Season to taste"
        ]
        
        new_steps, new_step_times = StepSplitter.split_recipe_steps(original_steps)
        
        # Should have more steps than original due to splitting
        assert len(new_steps) > len(original_steps)
        assert len(new_steps) == len(new_step_times)
        
        # All step times should be positive integers
        assert all(isinstance(time, int) and time > 0 for time in new_step_times)
        
        # Should contain split instructions
        step_text = " ".join(new_steps).lower()
        assert "simmer" in step_text
        assert "bake" in step_text
        assert "cook pasta" in step_text
        assert "drain" in step_text
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        # Empty string
        result = StepSplitter.split_step("")
        assert len(result) == 0 or (len(result) == 1 and not result[0].instruction.strip())
        
        # Very short text
        result = StepSplitter.split_step("Mix")
        assert len(result) == 1
        
        # Multiple conjunctions without clear times
        result = StepSplitter.split_step("Mix ingredients, then stir, then taste")
        # Should handle gracefully
        assert len(result) >= 1
    
    def test_time_extraction_edge_cases(self):
        """Test time extraction edge cases"""
        # Seconds (should convert to minutes)
        assert StepSplitter.extract_time_from_text("Cook for 90 seconds") == (1, "90 seconds")  # 1 minute minimum
        
        # Zero time
        assert StepSplitter.extract_time_from_text("Cook for 0 minutes") == (0, "0 minutes")
        
        # Negative time should not be found
        assert StepSplitter.extract_time_from_text("Cook for -5 minutes") == (None, None)
    
    def test_real_world_examples(self):
        """Test with real-world recipe step examples"""
        examples = [
            "Preheat oven to 350°F. Bake for 25 minutes, then remove and let cool for 10 minutes",
            "Sauté onions for 5 minutes until translucent, then add garlic and cook for 1 minute more",
            "Bring water to boil for 3 minutes, add pasta and cook for 10-12 minutes until al dente",
            "Marinate chicken for 2 hours. Heat grill and cook for 6 minutes per side",
            "Mix dry ingredients. In separate bowl, whisk wet ingredients for 2 minutes, then combine"
        ]
        
        for example in examples:
            result = StepSplitter.split_step(example)
            assert len(result) >= 1
            
            # Should extract at least one time from multi-time examples
            if StepSplitter.has_multiple_time_instructions(example):
                times = [step.time_minutes for step in result if step.time_minutes is not None]
                assert len(times) >= 1