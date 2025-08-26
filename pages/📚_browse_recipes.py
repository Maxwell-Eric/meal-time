# pages/📚_browse_recipes.py
import streamlit as st
from src.meal_time_logic.services.recipe_service import RecipeService
from src.components.recipe_browser import RecipeBrowser


def main():
    """Browse, search, and edit existing recipes"""

    st.set_page_config(
        page_title="Browse Recipes - Meal Time",
        page_icon="📋",
        layout="wide"
    )

    st.title("📋 Browse & Edit Recipes")

    # Initialize browser component
    browser = RecipeBrowser(get_recipe_service())
    browser.render()


def get_recipe_service() -> RecipeService:
    """Get or initialize the recipe service"""
    if 'recipe_service' not in st.session_state:
        st.error("⚠️ Recipe service not initialized. Please go back to the home page first.")
        if st.button("🏠 Go to Home"):
            st.switch_page("Home.py")
        st.stop()

    return st.session_state.recipe_service


if __name__ == "__main__":
    main()
