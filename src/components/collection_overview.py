# src/components/collection_overview.py
import streamlit as st
from src.meal_time_logic.services.recipe_service import RecipeService


class CollectionOverview:
    """Component for displaying recipe collection overview statistics"""

    def __init__(self, service: RecipeService):
        self.service = service

    def render(self) -> None:
        """Render the collection overview section"""
        st.subheader("📊 Collection Overview")

        stats = self._calculate_stats()
        self._render_metrics(stats)
        self._render_progress_bar(stats)
        self._render_completion_tip(stats)

    def _calculate_stats(self) -> dict:
        """Calculate collection statistics"""
        recipes = self.service.recipes

        return {
            'total_recipes': len(recipes),
            'total_steps': sum(len(r.steps) for r in recipes),
            'recipes_with_complete_times': sum(
                1 for r in recipes
                if r.step_times and len(r.step_times) == len(r.steps)
            ),
            'total_cooking_time': sum(
                sum(r.step_times) for r in recipes if r.step_times
            )
        }

    def _render_metrics(self, stats: dict) -> None:
        """Render the main metrics row"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Recipes", stats['total_recipes'])

        with col2:
            st.metric("Total Steps", stats['total_steps'])

        with col3:
            self._render_completion_metric(stats)

        with col4:
            self._render_time_metric(stats)

    def _render_completion_metric(self, stats: dict) -> None:
        """Render the timing completion metric"""
        complete = stats['recipes_with_complete_times']
        total = stats['total_recipes']

        completion_rate = f"{complete}/{total}"
        completion_pct = (complete / total * 100) if total > 0 else 0

        st.metric("Timing Complete", completion_rate, f"{completion_pct:.1f}%")

    def _render_time_metric(self, stats: dict) -> None:
        """Render the total cooking time metric"""
        total_minutes = stats['total_cooking_time']
        hours = total_minutes // 60
        minutes = total_minutes % 60

        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        st.metric("Total Cook Time", time_str)

    def _render_progress_bar(self, stats: dict) -> None:
        """Render the completion progress bar"""
        if stats['total_recipes'] == 0:
            return

        progress = stats['recipes_with_complete_times'] / stats['total_recipes']
        st.progress(progress)

    def _render_completion_tip(self, stats: dict) -> None:
        """Render tip if completion is not 100%"""
        complete = stats['recipes_with_complete_times']
        total = stats['total_recipes']

        if complete < total:
            missing_count = total - complete
            st.info(
                f"💡 {missing_count} recipe(s) need timing information. "
                f"Use bulk operations below to fix this!"
            )
            