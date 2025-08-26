# src/components/problem_recipes.py
import streamlit as st
from typing import List, Dict, Any
from src.meal_time_logic.services.recipe_service import RecipeService
from src.meal_time_logic.models.recipe import Recipe


class ProblemRecipes:
    """Component for identifying and fixing recipe issues"""

    def __init__(self, service: RecipeService):
        self.service = service

    def render(self) -> None:
        """Render the problem recipes section"""
        st.subheader("⚠️ Recipes Needing Attention")

        problem_recipes = self._identify_problem_recipes()

        if not problem_recipes:
            st.success("✅ All recipes look good! No issues found.")
            return

        st.write(f"Found {len(problem_recipes)} recipe(s) with issues:")

        for problem in problem_recipes:
            self._render_problem_recipe(problem)

    def _identify_problem_recipes(self) -> List[Dict[str, Any]]:
        """Identify recipes with various issues"""
        problem_recipes = []

        for recipe in self.service.recipes:
            issues = self._check_recipe_issues(recipe)

            if issues:
                problem_recipes.append({
                    'recipe': recipe,
                    'issues': issues
                })

        return problem_recipes

    def _check_recipe_issues(self, recipe: Recipe) -> List[str]:
        """Check a single recipe for issues"""
        issues = []

        # Check for missing step times
        if not recipe.step_times:
            issues.append("❌ No step times")
        elif len(recipe.step_times) != len(recipe.steps):
            issues.append("⚠️ Step time count mismatch")

        # Check for missing total time
        if not recipe.total_time and recipe.step_times:
            issues.append("📝 Missing total time")

        # Check for empty content
        if not recipe.ingredients:
            issues.append("🥬 No ingredients")
        if not recipe.steps:
            issues.append("📋 No steps")

        # Check for problematic step times
        if recipe.step_times:
            issues.extend(self._check_timing_issues(recipe.step_times))

        return issues

    def _check_timing_issues(self, step_times: List[int]) -> List[str]:
        """Check for timing-related issues"""
        issues = []

        very_short = sum(1 for t in step_times if t < 1)
        very_long = sum(1 for t in step_times if t > 120)  # 2 hours

        if very_short > 0:
            issues.append(f"⏱️ {very_short} step(s) < 1 minute")
        if very_long > 0:
            issues.append(f"⏰ {very_long} step(s) > 2 hours")

        return issues

    def _render_problem_recipe(self, problem: Dict[str, Any]) -> None:
        """Render a single problem recipe card"""
        recipe = problem['recipe']
        issues = problem['issues']

        with st.expander(f"⚠️ {recipe.name} - {len(issues)} issue(s)", expanded=False):
            # List issues
            for issue in issues:
                st.write(f"• {issue}")

            # Action buttons
            self._render_problem_recipe_actions(recipe)

    def _render_problem_recipe_actions(self, recipe: Recipe) -> None:
        """Render action buttons for problem recipe"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(f"🔧 Auto Fix", key=f"fix_{recipe.name}"):
                self._fix_recipe_issues(recipe)

        with col2:
            if st.button(f"✏️ Edit Recipe", key=f"edit_problem_{recipe.name}"):
                st.session_state.selected_recipes = [recipe.name]
                st.switch_page("pages/📚_browse_recipes.py")

        with col3:
            if st.button(f"📊 Analyze", key=f"analyze_problem_{recipe.name}"):
                self._analyze_problem_recipe(recipe)

    def _fix_recipe_issues(self, recipe: Recipe) -> None:
        """Attempt to automatically fix common recipe issues"""
        with st.spinner(f"Fixing issues in {recipe.name}..."):
            try:
                # Process step times
                enhanced_recipe = self.service.process_recipe_step_times(recipe)

                # Update total time if missing
                if not enhanced_recipe.total_time and enhanced_recipe.step_times:
                    enhanced_recipe.total_time = sum(enhanced_recipe.step_times)

                # Update the recipe
                self.service.update_recipe(enhanced_recipe)
                st.success(f"✅ Fixed issues in {recipe.name}!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error fixing {recipe.name}: {e}")

    def _analyze_problem_recipe(self, recipe: Recipe) -> None:
        """Analyze a problem recipe and show results"""
        try:
            analysis = self.service.get_step_time_analysis(recipe)
            st.json(analysis)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
