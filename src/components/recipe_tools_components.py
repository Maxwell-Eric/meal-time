# components/recipe_tools_components.py (REPLACEMENT)
import streamlit as st
from src.meal_time_logic.services.recipe_service import RecipeService
from src.components.collection_overview import CollectionOverview
from src.components.bulk_operations import BulkOperations
from src.components.analysis_tools import AnalysisTools
from src.components.problem_recipes import ProblemRecipes


def show(service: RecipeService):
    """Show recipe tools and bulk operations"""

    if not service.recipes:
        show_empty_tools_state()
        return

    # Render main components
    overview = CollectionOverview(service)
    overview.render()

    st.markdown("---")

    bulk_ops = BulkOperations(service)
    bulk_ops.render()

    st.markdown("---")

    analysis = AnalysisTools(service)
    analysis.render()

    st.markdown("---")

    problems = ProblemRecipes(service)
    problems.render()


def show_empty_tools_state():
    """Show empty state for tools page"""
    st.info("📚 No recipes found. Add some recipes first to use these tools!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Recipe", type="primary"):
            st.switch_page("pages/➕_add_recipe.py")
    with col2:
        if st.button("🌐 Import from Web"):
            st.switch_page("components/import_recipe_from_web.py")
