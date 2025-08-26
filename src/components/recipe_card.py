# src/components/recipe_card.py
import streamlit as st
from typing import Optional
from src.meal_time_logic.models.recipe import Recipe
from src.meal_time_logic.services.recipe_service import RecipeService


class RecipeCard:
    """Component for displaying a single recipe card with all interactions"""

    def __init__(self, service: RecipeService, recipe: Recipe):
        self.service = service
        self.recipe = recipe

    def render(self) -> None:
        """Render the complete recipe card"""
        with st.expander(f"🍽️ {self.recipe.name}", expanded=False):
            self._render_stats()
            self._render_preview_toggle()
            self._render_action_buttons()
            self._render_conditional_sections()

    def _render_stats(self) -> None:
        """Render the recipe statistics row"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Ingredients", len(self.recipe.ingredients))
        with col2:
            st.metric("Steps", len(self.recipe.steps))
        with col3:
            self._render_time_metric()
        with col4:
            self._render_completion_status()

    def _render_time_metric(self) -> None:
        """Render time information metric"""
        if self.recipe.step_times:
            total_time = sum(self.recipe.step_times)
            st.metric("Est. Time", f"{total_time} min")
        elif self.recipe.total_time:
            st.metric("Total Time", f"{self.recipe.total_time} min")
        else:
            st.write("⚠️ No timing info")

    def _render_completion_status(self) -> None:
        """Render timing completion status"""
        if self._is_timing_complete():
            st.success("✅ Complete")
        else:
            st.warning("⚠️ Needs timing")

    def _render_preview_toggle(self) -> None:
        """Render the preview toggle and content"""
        preview_key = f"preview_{self.recipe.name}"
        if st.checkbox("👀 Show Preview", key=preview_key):
            self._render_preview()

    def _render_preview(self) -> None:
        """Render recipe preview content"""
        col1, col2 = st.columns([1, 1])

        with col1:
            self._render_ingredients_preview()
        with col2:
            self._render_steps_preview()

    def _render_ingredients_preview(self) -> None:
        """Render ingredients preview"""
        st.markdown("**🥬 Ingredients:**")
        max_items = 8
        for ingredient in self.recipe.ingredients[:max_items]:
            st.write(f"• {ingredient}")
        if len(self.recipe.ingredients) > max_items:
            st.write(f"... and {len(self.recipe.ingredients) - max_items} more")

    def _render_steps_preview(self) -> None:
        """Render steps preview"""
        st.markdown("**👨‍🍳 Instructions:**")
        max_steps = 5
        for i, step in enumerate(self.recipe.steps[:max_steps], 1):
            time_info = self._get_step_time_info(i - 1)
            step_preview = self._truncate_step(step)
            st.write(f"{i}.{time_info} {step_preview}")
        if len(self.recipe.steps) > max_steps:
            st.write(f"... and {len(self.recipe.steps) - max_steps} more steps")

    def _render_action_buttons(self) -> None:
        """Render all action buttons"""
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            self._render_edit_button()
        with col2:
            self._render_fix_times_button()
        with col3:
            self._render_analyze_button()
        with col4:
            self._render_cook_button()
        with col5:
            self._render_delete_button()

    def _render_edit_button(self) -> None:
        """Render edit button and handle click"""
        edit_key = f"edit_{self.recipe.name}"
        if st.button("✏️ Edit", key=edit_key):
            st.session_state[f"editing_{self.recipe.name}"] = True
            st.rerun()

    def _render_fix_times_button(self) -> None:
        """Render fix times button and handle click"""
        st.button("⏱️ Fix Times", disabled=True, key=f"times_{self.recipe.name}",
                  help="Temporarily disabled - step parser needs fixes")

    def _render_analyze_button(self) -> None:
        """Render analyze button and handle click"""
        st.button("📊 Analyze", disabled=True, key=f"analyze_{self.recipe.name}",
                  help="Temporarily disabled - analysis needs fixes")

    def _render_cook_button(self) -> None:
        """Render cook button and handle click"""
        if st.button("🍽️ Cook", key=f"cook_{self.recipe.name}"):
            st.session_state.selected_recipes = [self.recipe.name]
            st.switch_page("pages/🍽️_plan_meal.py")

    def _render_delete_button(self) -> None:
        """Render delete button and handle click"""
        if st.button("🗑️ Delete", key=f"delete_{self.recipe.name}", type="secondary"):
            st.session_state[f"deleting_{self.recipe.name}"] = True
            st.rerun()

    def _render_conditional_sections(self) -> None:
        """Render sections that appear conditionally"""
        self._render_editor_if_editing()
        self._render_analysis_if_requested()
        self._render_delete_confirmation_if_requested()

    def _render_editor_if_editing(self) -> None:
        """Render recipe editor if editing mode is active"""
        if st.session_state.get(f"editing_{self.recipe.name}", False):
            st.markdown("---")
            from src.components.recipe_editor import show_recipe_editor
            show_recipe_editor(self.service, self.recipe)
            if st.button("✅ Done Editing", key=f"done_{self.recipe.name}"):
                st.session_state[f"editing_{self.recipe.name}"] = False
                st.rerun()

    def _render_analysis_if_requested(self) -> None:
        """Render recipe analysis if requested"""
        if st.session_state.get(f"analyzing_{self.recipe.name}", False):
            st.markdown("---")
            from src.components.recipe_analysis import RecipeAnalysis
            analysis_component = RecipeAnalysis(self.service, self.recipe)
            analysis_component.render()
            if st.button("❌ Close Analysis", key=f"close_analysis_{self.recipe.name}"):
                st.session_state[f"analyzing_{self.recipe.name}"] = False
                st.rerun()

    def _render_delete_confirmation_if_requested(self) -> None:
        """Render delete confirmation if requested"""
        if st.session_state.get(f"deleting_{self.recipe.name}", False):
            st.markdown("---")
            from src.components.delete_confirmation import DeleteConfirmation
            delete_component = DeleteConfirmation(self.service, self.recipe)
            delete_component.render()

    # Helper methods
    def _is_timing_complete(self) -> bool:
        """Check if recipe has complete timing information"""
        return (self.recipe.step_times and
                len(self.recipe.step_times) == len(self.recipe.steps))

    def _get_step_time_info(self, step_index: int) -> str:
        """Get time information for a step"""
        if (self.recipe.step_times and
                step_index < len(self.recipe.step_times)):
            return f" ({self.recipe.step_times[step_index]} min)"
        return ""

    def _truncate_step(self, step: str, max_length: int = 60) -> str:
        """Truncate step text if too long"""
        return step[:max_length] + "..." if len(step) > max_length else step

    def _fix_recipe_times(self) -> None:
        """Fix/enhance recipe step times"""
        with st.spinner("Enhancing step times..."):
            try:
                enhanced = self.service.process_recipe_step_times(self.recipe)
                self.service.update_recipe(enhanced)
                st.success("✅ Step times updated!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


# Convenience function for backwards compatibility
def show_recipe_card(service: RecipeService, recipe: Recipe) -> None:
    """Convenience function to render a recipe card"""
    card = RecipeCard(service, recipe)
    card.render()
