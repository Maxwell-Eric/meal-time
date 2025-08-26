# meal_time_logic/exceptions.py

class MealTimeException(Exception):
    """Base exception for meal-time app"""
    pass


class RecipeNotFoundException(MealTimeException):
    """Raised when a recipe is not found"""
    def __init__(self, recipe_name: str):
        self.recipe_name = recipe_name
        super().__init__(f"Recipe '{recipe_name}' not found")


class InvalidRecipeException(MealTimeException):
    """Raised when a recipe has invalid data"""
    def __init__(self, recipe_name: str, reason: str):
        self.recipe_name = recipe_name
        self.reason = reason
        super().__init__(f"Invalid recipe '{recipe_name}': {reason}")


class TimelineException(MealTimeException):
    """Raised when timeline generation fails"""
    pass


class ImpossibleTimingException(TimelineException):
    """Raised when requested timing is impossible"""
    def __init__(self, message: str, required_start_time=None):
        self.required_start_time = required_start_time
        super().__init__(message)


class StepTimePredictionException(MealTimeException):
    """Raised when ML step time prediction fails"""
    pass
