# src/components/bulk_operations.py
import streamlit as st
from src.meal_time_logic.services.recipe_service import RecipeService


class BulkOperations:
    """Component for bulk recipe operations"""

    def __init__(self, service: RecipeService):
        self.service = service

    def render(self) -> None:
        """Render the bulk operations section"""
        st.subheader("🚀 Bulk Operations")
        st.markdown("Perform operations on all recipes at once:")

        self._render_operation_buttons()
        self._render_operation_details()

    def _render_operation_buttons(self) -> None:
        """Render the main operation buttons"""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.button("🎯 Enhance All Recipe Times", disabled=True, use_container_width=True,
                      help="Temporarily disabled - step parser needs fixes")

        with col2:
            st.button("🔧 Generate Missing Times", disabled=True, use_container_width=True,
                      help="Temporarily disabled - step parser needs fixes")

        with col3:
            if st.button("🧹 Clean Recipe Data", use_container_width=True):
                self._clean_recipe_data()

    def _render_operation_details(self) -> None:
        """Render operation descriptions in an expander"""
        with st.expander("ℹ️ What do these operations do?", expanded=False):
            st.markdown("""
            **🎯 Enhance All Recipe Times:**
            - Re-analyzes all recipes to improve step time detection
            - Splits steps that contain multiple timing instructions
            - Finds times that might have been missed initially

            **🔧 Generate Missing Times:**
            - Uses AI to predict times for steps without explicit timing
            - Only affects recipes that are missing step times
            - Uses machine learning based on cooking action keywords

            **🧹 Clean Recipe Data:**
            - Removes empty ingredients or steps
            - Standardizes formatting
            - Updates total times based on step times
            """)

    def _enhance_all_times(self) -> None:
        """Enhanced all recipe times with progress tracking"""
        recipes = self.service.recipes
        if not recipes:
            st.info("No recipes to enhance.")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            enhanced_count = 0

            for i, recipe in enumerate(recipes):
                # Update progress
                progress = (i + 1) / len(recipes)
                progress_bar.progress(progress)
                status_text.text(f"Processing recipe {i + 1}/{len(recipes)}: {recipe.name}")

                original_step_count = len(recipe.steps)
                enhanced_recipe = self.service.process_recipe_step_times(recipe)

                # Only update if we made improvements
                if (len(enhanced_recipe.steps) != original_step_count or
                        enhanced_recipe.step_times != recipe.step_times):
                    self.service.recipes[i] = enhanced_recipe
                    enhanced_count += 1

            if enhanced_count > 0:
                self.service._save()  # Save changes
                st.success(f"✅ Enhanced {enhanced_count} recipes with better step timing!")
            else:
                st.info("ℹ️ All recipes already have good step timing.")

        except Exception as e:
            st.error(f"❌ Error enhancing recipes: {e}")
        finally:
            progress_bar.empty()
            status_text.empty()

    def _generate_missing_times(self) -> None:
        """Generate missing step times"""
        with st.spinner("Generating missing step times..."):
            try:
                # Check how many recipes need processing first
                recipes_needing_times = [
                    r for r in self.service.recipes
                    if not r.step_times or len(r.step_times) != len(r.steps)
                ]

                if not recipes_needing_times:
                    st.info("All recipes already have complete step times!")
                    return

                # Process the recipes
                self.service.generate_missing_step_times()

                st.success(f"✅ Generated missing step times for {len(recipes_needing_times)} recipes!")

                # Don't auto-rerun, let the user refresh manually if needed
                st.info("💡 Refresh the page to see updated statistics.")

            except Exception as e:
                st.error(f"❌ Error generating step times: {e}")
                # Debug info
                st.write("Error type:", type(e).__name__)
                if hasattr(e, '__traceback__'):
                    import traceback
                    st.code(traceback.format_exc())

    def _clean_recipe_data(self) -> None:
        """Clean up recipe data"""
        with st.spinner("Cleaning recipe data..."):
            try:
                cleaned_count = 0

                for i, recipe in enumerate(self.service.recipes):
                    # Clean ingredients (remove empty ones)
                    original_ing_count = len(recipe.ingredients)
                    recipe.ingredients = [ing.strip() for ing in recipe.ingredients if ing.strip()]

                    # Clean steps (remove empty ones)
                    original_step_count = len(recipe.steps)
                    recipe.steps = [step.strip() for step in recipe.steps if step.strip()]

                    # Update total time if missing but step times exist
                    if not recipe.total_time and recipe.step_times:
                        recipe.total_time = sum(recipe.step_times)

                    # Check if anything was cleaned
                    if (len(recipe.ingredients) != original_ing_count or
                            len(recipe.steps) != original_step_count or
                            (not recipe.total_time and recipe.step_times)):
                        cleaned_count += 1

                if cleaned_count > 0:
                    self.service._save()
                    st.success(f"✅ Cleaned up {cleaned_count} recipes!")
                else:
                    st.info("ℹ️ All recipes are already clean.")

            except Exception as e:
                st.error(f"❌ Error cleaning recipes: {e}")
