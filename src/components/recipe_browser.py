# src/components/recipe_browser.py
import streamlit as st
from typing import List
from src.meal_time_logic.services.recipe_service import RecipeService
from src.meal_time_logic.models.recipe import Recipe
from src.components.recipe_card import RecipeCard
from src.components.search_filters import SearchFilters
from src.meal_time_logic.services.recipe_filter_service import RecipeFilterService


class RecipeBrowser:
    """Main browser component that orchestrates recipe browsing functionality"""

    def __init__(self, service: RecipeService):
        self.service = service
        self.filter_service = RecipeFilterService()
        self.search_filters = SearchFilters()

    def render(self) -> None:
        """Render the complete recipe browser"""
        if not self.service.recipes:
            self._render_empty_state()
            return

        # Render search and filter controls
        filter_criteria = self.search_filters.render(self.service)

        # Apply filters
        filtered_recipes = self.filter_service.filter_recipes(
            self.service.recipes,
            filter_criteria
        )

        if not filtered_recipes:
            st.info("No recipes found matching your search.")
            return

        # Show results
        self._render_results(filtered_recipes)

    def _render_empty_state(self) -> None:
        """Show empty state when no recipes exist"""
        st.info("📚 No recipes found. Let's add some!")

        st.markdown("""
        **Get started by:**
        - 🌐 Importing a recipe from a website URL
        - ➕ Manually entering a favorite recipe
        - 📖 Adding multiple recipes to build your collection
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌐 Import from Web", type="primary"):
                st.switch_page("pages/🌐_import_from_web.py")
        with col2:
            if st.button("➕ Add Recipe Manually"):
                st.switch_page("pages/➕_add_recipe.py")

    def _render_results(self, recipes: List[Recipe]) -> None:
        """Render the filtered recipe results"""
        st.markdown(f"**Found {len(recipes)} recipe(s)**")

        for recipe in recipes:
            card = RecipeCard(self.service, recipe)
            card.render()
