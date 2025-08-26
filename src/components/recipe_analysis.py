# src/components/recipe_analysis.py
import streamlit as st
from src.meal_time_logic.models.recipe import Recipe
from src.meal_time_logic.services.recipe_service import RecipeService


class RecipeAnalysis:
    """Component for displaying detailed recipe analysis"""

    def __init__(self, service: RecipeService, recipe: Recipe):
        self.service = service
        self.recipe = recipe

    def render(self) -> None:
        """Render the complete recipe analysis"""
        st.markdown(f"### 📊 Analysis: {self.recipe.name}")

        try:
            analysis = self.service.get_step_time_analysis(self.recipe)
            self._render_overview_metrics(analysis)
            self._render_confidence_breakdown(analysis)
            self._render_issues_needing_review(analysis)
            self._render_step_details(analysis)
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")

    def _render_overview_metrics(self, analysis: dict) -> None:
        """Render overview metrics row"""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Original Steps", analysis['original_steps'])
        with col2:
            st.metric("Processed Steps", analysis['processed_steps'])
        with col3:
            st.metric("Total Time", f"{analysis['total_time_minutes']} min")
        with col4:
            extracted = analysis['extracted_times']
            processed = analysis['processed_steps']
            st.metric("Times Found", f"{extracted}/{processed}")

    def _render_confidence_breakdown(self, analysis: dict) -> None:
        """Render confidence breakdown info"""
        conf = analysis['confidence_breakdown']
        st.info(
            f"📊 **Time Sources**: "
            f"{conf['extracted']} extracted, "
            f"{conf['predicted']} predicted, "
            f"{conf['user_set']} user-set"
        )

    def _render_issues_needing_review(self, analysis: dict) -> None:
        """Render issues that need user review"""
        if analysis['needs_review']:
            issue_count = len(analysis['needs_review'])
            st.warning(f"⚠️ **{issue_count} step(s) need review:**")
            for issue in analysis['needs_review']:
                st.write(f"• Step {issue['step_number']}: {issue['reason']}")
        else:
            st.success("✅ All step times look good!")

    def _render_step_details(self, analysis: dict) -> None:
        """Render detailed step information"""
        with st.expander("🔍 Step Details", expanded=False):
            confidence_emojis = {
                'extracted': '✅',
                'predicted': '🤖',
                'user_set': '✏️'
            }

            for i, (step, time_val, conf) in enumerate(zip(
                    analysis['expanded_steps'],
                    analysis['step_times'],
                    analysis['confidence_info']
            ), 1):
                emoji = confidence_emojis.get(conf, '❓')
                st.write(f"**{i}. {emoji} [{time_val} min]** {step}")