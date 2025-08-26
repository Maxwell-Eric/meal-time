# src/components/delete_confirmation.py
import streamlit as st
from src.meal_time_logic.models.recipe import Recipe
from src.meal_time_logic.services.recipe_service import RecipeService


class DeleteConfirmation:
    """Component for handling recipe deletion confirmation"""

    def __init__(self, service: RecipeService, recipe: Recipe):
        self.service = service
        self.recipe = recipe

    def render(self) -> None:
        """Render the delete confirmation dialog"""
        st.warning(f"⚠️ **Delete '{self.recipe.name}'?**")
        st.write("This action cannot be undone.")

        col1, col2 = st.columns(2)

        with col1:
            self._render_confirm_button()
        with col2:
            self._render_cancel_button()

    def _render_confirm_button(self) -> None:
        """Render confirmation button and handle deletion"""
        confirm_key = f"confirm_delete_{self.recipe.name}"
        if st.button("🗑️ Yes, Delete", key=confirm_key, type="secondary"):
            try:
                self.service.delete_recipe(self.recipe.name)
                st.success(f"✅ Deleted '{self.recipe.name}'")
                # Clear the deletion state
                st.session_state[f"deleting_{self.recipe.name}"] = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    def _render_cancel_button(self) -> None:
        """Render cancel button and handle cancellation"""
        cancel_key = f"cancel_delete_{self.recipe.name}"
        if st.button("❌ Cancel", key=cancel_key):
            # Clear the deletion state
            st.session_state[f"deleting_{self.recipe.name}"] = False
            st.rerun()
