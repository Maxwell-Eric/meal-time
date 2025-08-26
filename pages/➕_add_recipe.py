# pages/1_➕_Add_Recipe.py
import streamlit as st
from src.meal_time_logic.models.recipe import Recipe

st.set_page_config(
    page_title="Add Recipe - Meal Time",
    page_icon="➕",
    layout="wide"
)

# Get the recipe service from session state
if 'recipe_service' not in st.session_state:
    st.error("⚠️ Recipe service not initialized. Please go back to the home page first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()

service = st.session_state.recipe_service

st.title("➕ Add New Recipe")
st.markdown("Create a new recipe by filling out the form below. Step times will be automatically detected!")

def show_manual_recipe_form():
    """Show form to add a recipe manually"""

    with st.form("add_recipe_form", clear_on_submit=True):
        # Basic info section
        st.subheader("📝 Basic Information")

        recipe_name = st.text_input(
            "Recipe Name*:",
            placeholder="e.g., Chocolate Chip Cookies",
            help="Give your recipe a unique, descriptive name"
        )

        col1, col2 = st.columns(2)
        with col1:
            prep_time = st.number_input(
                "Prep Time (minutes):",
                min_value=0,
                value=15,
                help="Time needed for preparation (chopping, mixing, etc.)"
            )
        with col2:
            cook_time = st.number_input(
                "Cook Time (minutes):",
                min_value=0,
                value=30,
                help="Active cooking time (baking, frying, etc.)"
            )

        # Ingredients section
        st.subheader("🥬 Ingredients")
        ingredients_text = st.text_area(
            "Enter ingredients (one per line):",
            placeholder="2 cups all-purpose flour\n1 cup granulated sugar\n2 large eggs\n1 tsp vanilla extract\n...",
            height=150,
            help="List each ingredient on a separate line. Include quantities and units."
        )

        # Steps section
        st.subheader("👨‍🍳 Instructions")
        st.markdown("*Include timing information when possible (e.g., 'Bake for 15 minutes' or 'Simmer until tender')*")

        steps_text = st.text_area(
            "Enter cooking steps (one per line):",
            placeholder="Preheat oven to 350°F\nMix flour and sugar in a large bowl\nAdd eggs and vanilla, stir until combined\nBake for 12-15 minutes until golden\nCool for 5 minutes before serving",
            height=200,
            help="Write clear, actionable steps. Include times when you know them - the system will detect and use them automatically."
        )

        # Advanced options
        with st.expander("🔧 Advanced Options", expanded=False):
            st.markdown("**Override automatic timing:**")
            col1, col2 = st.columns(2)
            with col1:
                custom_total = st.checkbox("Set custom total time")
                if custom_total:
                    total_time = st.number_input("Total time (minutes):", min_value=1, value=45)
                else:
                    total_time = None

            with col2:
                auto_enhance = st.checkbox("Auto-enhance step timing", value=True,
                                           help="Automatically detect and improve step timing information")

        # Submit button
        submitted = st.form_submit_button("➕ Add Recipe", type="primary")

        if submitted:
            # Validate inputs
            if not recipe_name.strip():
                st.error("❌ Recipe name is required!")
                return

            if not ingredients_text.strip():
                st.error("❌ At least one ingredient is required!")
                return

            if not steps_text.strip():
                st.error("❌ At least one step is required!")
                return

            # Parse ingredients and steps
            ingredients = [ing.strip() for ing in ingredients_text.strip().split('\n') if ing.strip()]
            steps = [step.strip() for step in steps_text.strip().split('\n') if step.strip()]

            # Create recipe
            new_recipe = Recipe(
                name=recipe_name.strip(),
                ingredients=ingredients,
                steps=steps,
                prep_time=prep_time if prep_time > 0 else None,
                cook_time=cook_time if cook_time > 0 else None,
                total_time=total_time if custom_total and total_time else None,
                step_times=[]
            )

            # Add recipe
            try:
                if auto_enhance:
                    # Use the service method that processes step times automatically
                    processed_recipe = service.add_recipe_with_time_processing(new_recipe)
                    st.success(f"✅ Successfully added '{recipe_name}'!")
                    st.success(f"🤖 Generated step times automatically!")

                    # Show the processed recipe
                    show_recipe_success(processed_recipe)

                else:
                    # Add without processing
                    service.add_recipe(new_recipe)
                    st.success(f"✅ Successfully added '{recipe_name}'!")
                    st.info("💡 You can add step times later using the Recipe Tools page.")

                # Show next steps
                show_success_actions(recipe_name)

            except Exception as e:
                st.error(f"❌ Error adding recipe: {e}")


def show_recipe_success(recipe):
    """Show success information about the added recipe"""

    st.markdown("### 🎉 Recipe Added Successfully!")

    # Show recipe summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Ingredients", len(recipe.ingredients))
    with col2:
        st.metric("Steps", len(recipe.steps))
    with col3:
        st.metric("Step Times", len(recipe.step_times))
    with col4:
        if recipe.step_times:
            total = sum(recipe.step_times)
            st.metric("Est. Time", f"{total} min")
        elif recipe.total_time:
            st.metric("Total Time", f"{recipe.total_time} min")

    # Show step timing preview
    with st.expander("👀 Step Timing Preview", expanded=True):
        if recipe.step_times:
            for i, (step, time_val) in enumerate(zip(recipe.steps, recipe.step_times), 1):
                st.write(f"**{i}. [{time_val} min]** {step[:80]}{'...' if len(step) > 80 else ''}")
        else:
            st.info("No step times generated. You can add them later.")


def show_success_actions(recipe_name):
    """Show action buttons after successful recipe addition"""

    st.markdown("### 🎯 What's Next?")

    col1, col2, col3, col4= st.columns(4)

    with col1:
        if st.button("🍽️ Plan a Meal with This Recipe", type="primary", use_container_width=True):
            # Navigate to plan meal page with this recipe selected
            st.session_state.selected_recipes = [recipe_name]
            st.switch_page("pages/🍽️_plan_meal.py")

    with col2:
        if st.button("✏️ Edit Recipe Details", use_container_width=True):
            st.switch_page("pages/3_📋_Browse_Recipes.py")

    with col3:
        if st.button("➕ Add Another Recipe", use_container_width=True):
            st.rerun()

    with col4:
        if st.button(f"🍽️ Cook", key=f"cook_{recipe.name}"):
            # Navigate to organize page with this recipe selected
            st.session_state.selected_recipes = [recipe.name]
            st.switch_page("pages/🍽️_plan_meal.py")


def show_recipe_tips():
    """Show helpful tips for adding recipes"""

    with st.expander("💡 Tips for Better Recipes", expanded=False):
        st.markdown("""
        **📝 Writing Great Steps:**
        - Include specific times: "Bake for 15 minutes" instead of "Bake until done"
        - Use clear action words: "Sauté", "Simmer", "Mix", "Chop"
        - Be specific about temperatures: "350°F oven" or "medium-high heat"

        **⏱️ Timing Detection:**
        - The system automatically finds times like "10 minutes", "1 hour", "2-3 minutes"
        - Steps without times get smart predictions based on the cooking action
        - You can always edit times later if needed

        **🥬 Ingredient Tips:**
        - Include quantities and units: "2 cups flour" not just "flour"
        - Be specific about types: "large eggs", "kosher salt", "extra-virgin olive oil"
        - List in order of use when possible

        **🎯 Recipe Organization:**
        - Break complex steps into smaller ones for better timing
        - Group similar prep work: "Dice onions and mince garlic"
        - End with serving/finishing steps: "Garnish and serve immediately"
        """)

    st.info(
        "💡 **Pro Tip**: After adding a recipe, try the 'Plan a Meal' feature to see how it coordinates with other dishes!")

# Call the main functions
show_manual_recipe_form()
show_recipe_tips()
