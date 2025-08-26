# src/components/search_filters.py
import streamlit as st
from typing import Dict, Any
from src.meal_time_logic.services.recipe_service import RecipeService


class SearchFilters:
    """Component for rendering search and filter controls"""

    def render(self, service: RecipeService) -> Dict[str, Any]:
        """Render search and filter controls, return filter criteria"""
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search = self._render_search_input()

        with col2:
            timing_filter = self._render_timing_filter()

        with col3:
            sort_by = self._render_sort_options()

        return {
            'search': search,
            'timing_filter': timing_filter,
            'sort_by': sort_by
        }

    def _render_search_input(self) -> str:
        """Render the search input field"""
        return st.text_input(
            "🔍 Search recipes:",
            placeholder="Type recipe name, ingredient, or cooking method...",
            help="Search in recipe names, ingredients, and steps"
        )

    def _render_timing_filter(self) -> str:
        """Render timing completeness filter"""
        return st.selectbox(
            "Timing Status:",
            ["All", "Complete", "Incomplete"],
            help="Filter by whether recipes have complete step timing"
        )

    def _render_sort_options(self) -> str:
        """Render sort options"""
        return st.selectbox(
            "Sort by:",
            ["Name", "Steps", "Time", "Recent"],
            help="How to order the recipes"
        )
