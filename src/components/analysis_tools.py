# src/components/analysis_tools.py
import streamlit as st
from collections import Counter
from src.meal_time_logic.services.recipe_service import RecipeService


class AnalysisTools:
    """Component for collection analysis and statistics"""

    def __init__(self, service: RecipeService):
        self.service = service

    def render(self) -> None:
        """Render the analysis tools section"""
        st.subheader("📈 Collection Analysis")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Show Detailed Stats", use_container_width=True):
                st.session_state.show_detailed_stats = True

        with col2:
            if st.button("🥕 Ingredient Analysis", use_container_width=True):
                st.session_state.show_ingredient_analysis = True

        # Render the requested analysis
        if st.session_state.get('show_detailed_stats', False):
            self._render_detailed_stats()

        if st.session_state.get('show_ingredient_analysis', False):
            self._render_ingredient_analysis()

    def _render_detailed_stats(self) -> None:
        """Show detailed collection statistics"""
        st.markdown("### 📊 Detailed Statistics")

        recipes = self.service.recipes
        step_times, recipe_times = self._collect_timing_data(recipes)

        if step_times:
            self._render_timing_metrics(step_times, recipe_times)
            self._render_step_distribution(step_times)

        self._render_complexity_stats(recipes)

        # Add close button
        if st.button("❌ Close Stats"):
            st.session_state.show_detailed_stats = False
            st.rerun()

    def _collect_timing_data(self, recipes):
        """Collect timing data from all recipes"""
        step_times = []
        recipe_times = []

        for recipe in recipes:
            if recipe.step_times:
                step_times.extend(recipe.step_times)
                recipe_times.append(sum(recipe.step_times))

        return step_times, recipe_times

    def _render_timing_metrics(self, step_times, recipe_times):
        """Render timing-related metrics"""
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_step = sum(step_times) / len(step_times)
            st.metric("Avg Step Time", f"{avg_step:.1f} min")

        with col2:
            avg_recipe = sum(recipe_times) / len(recipe_times) if recipe_times else 0
            st.metric("Avg Recipe Time", f"{avg_recipe:.0f} min")

        with col3:
            longest_recipe = max(recipe_times) if recipe_times else 0
            st.metric("Longest Recipe", f"{longest_recipe} min")

    def _render_step_distribution(self, step_times):
        """Render step time distribution"""
        st.markdown("**Step Time Distribution:**")

        quick_steps = sum(1 for t in step_times if t <= 5)
        medium_steps = sum(1 for t in step_times if 5 < t <= 20)
        long_steps = sum(1 for t in step_times if t > 20)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quick (≤5 min)", quick_steps)
        with col2:
            st.metric("Medium (5-20 min)", medium_steps)
        with col3:
            st.metric("Long (>20 min)", long_steps)

    def _render_complexity_stats(self, recipes):
        """Render recipe complexity statistics"""
        st.markdown("**Recipe Complexity:**")

        step_counts = [len(r.steps) for r in recipes]
        ingredient_counts = [len(r.ingredients) for r in recipes]

        col1, col2 = st.columns(2)

        with col1:
            if step_counts:
                avg_steps = sum(step_counts) / len(step_counts)
                max_steps = max(step_counts)
                st.write(f"**Steps per Recipe:** {avg_steps:.1f} average, {max_steps} maximum")

        with col2:
            if ingredient_counts:
                avg_ingredients = sum(ingredient_counts) / len(ingredient_counts)
                max_ingredients = max(ingredient_counts)
                st.write(f"**Ingredients per Recipe:** {avg_ingredients:.1f} average, {max_ingredients} maximum")

    def _render_ingredient_analysis(self) -> None:
        """Show ingredient usage analysis"""
        st.markdown("### 🥕 Ingredient Analysis")

        ingredient_data = self._collect_ingredient_data()

        if not ingredient_data['all_ingredients']:
            st.info("No ingredients found in recipes.")
            if st.button("❌ Close Analysis"):
                st.session_state.show_ingredient_analysis = False
                st.rerun()
            return

        self._render_common_ingredients(ingredient_data)
        self._render_ingredient_metrics(ingredient_data)

        # Add close button
        if st.button("❌ Close Analysis"):
            st.session_state.show_ingredient_analysis = False
            st.rerun()

    def _collect_ingredient_data(self):
        """Collect and process ingredient data"""
        all_ingredients = []
        ingredient_recipes = {}

        for recipe in self.service.recipes:
            for ingredient in recipe.ingredients:
                cleaned = ingredient.lower().strip()
                all_ingredients.append(cleaned)

                if cleaned not in ingredient_recipes:
                    ingredient_recipes[cleaned] = []
                ingredient_recipes[cleaned].append(recipe.name)

        return {
            'all_ingredients': all_ingredients,
            'ingredient_recipes': ingredient_recipes,
            'common_ingredients': Counter(all_ingredients).most_common(15)
        }

    def _render_common_ingredients(self, ingredient_data):
        """Render most common ingredients list"""
        st.markdown("**🏆 Most Used Ingredients:**")

        for i, (ingredient, count) in enumerate(ingredient_data['common_ingredients'], 1):
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                st.write(f"**{i}.**")
            with col2:
                st.write(ingredient.title())
            with col3:
                st.write(f"{count} recipes")

                # Show which recipes use this ingredient
                if st.button(f"👀 Show recipes", key=f"show_ingredient_{i}"):
                    st.write("Used in:")
                    for recipe_name in ingredient_data['ingredient_recipes'][ingredient]:
                        st.write(f"• {recipe_name}")

    def _render_ingredient_metrics(self, ingredient_data):
        """Render ingredient usage metrics"""
        unique_count = len(set(ingredient_data['all_ingredients']))
        total_uses = len(ingredient_data['all_ingredients'])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Unique Ingredients", unique_count)
        with col2:
            st.metric("Total Ingredient Uses", total_uses)
