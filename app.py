# streamlit/app.py
import streamlit as st
from src.meal_time_logic.services.recipe_service import RecipeService

st.set_page_config(
    page_title="Meal Time 🍴",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize recipe service and store in session state
@st.cache_resource
def get_recipe_service():
    try:
        service = RecipeService()
        return service
    except Exception as e:
        st.error(f"Error initializing recipe service: {e}")
        st.info("Make sure you have the required data directory and files set up.")
        st.stop()


# Store service in session state so other pages can access it
if 'recipe_service' not in st.session_state:
    st.session_state.recipe_service = get_recipe_service()

service = st.session_state.recipe_service

# HOME PAGE CONTENT
st.title("🍴 Welcome to Meal Time!")
st.markdown("*Your personal cooking timeline organizer*")

# Quick stats
st.subheader("📊 Your Recipe Collection")
recipes = service.recipes
total_recipes = len(recipes)

if total_recipes == 0:
    st.info("No recipes yet! Get started by adding your first recipe.")
else:
    # Calculate stats
    total_steps = sum(len(r.steps) for r in recipes)
    recipes_with_times = sum(1 for r in recipes
                             if r.step_times and len(r.step_times) == len(r.steps))
    total_cooking_time = sum(sum(r.step_times) for r in recipes if r.step_times)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Recipes", total_recipes)

    with col2:
        st.metric("Recipe Steps", total_steps)

    with col3:
        completion_rate = f"{recipes_with_times}/{total_recipes}"
        st.metric("Timing Complete", completion_rate)

    with col4:
        hours = total_cooking_time // 60
        minutes = total_cooking_time % 60
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        st.metric("Total Cook Time", time_str)

# Quick actions
st.markdown("---")
st.subheader("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🍽️ Plan a Meal", type="primary", use_container_width=True):
        st.switch_page("pages/🍽️_plan_meal.py")

with col2:
    if st.button("➕ Add New Recipe", use_container_width=True):
        st.switch_page("pages/➕_add_recipe.py")

with col3:
    if st.button("🌐 Import from Web", use_container_width=True):
        st.switch_page("pages/🌐_import_from_web.py")

# Getting started or recent recipes
if not service.recipes:
    st.markdown("---")
    st.subheader("🚀 Getting Started")

    st.markdown("""
    Welcome to Meal Time! Here's how to get started:

    **1. 📝 Add Your First Recipe**
    - Use "Add Recipe" to manually enter a favorite recipe
    - Or try "Import from Web" to grab recipes from cooking websites

    **2. ⏱️ Automatic Timing**
    - Meal Time automatically detects cooking times in your steps
    - Uses AI to predict timing for steps without explicit times
    - You can always edit times manually

    **3. 🍽️ Plan Your Meals**
    - Select multiple recipes to cook together
    - Get a coordinated timeline so everything finishes simultaneously
    - Never overcook or undercook again!
    """)

else:
    st.markdown("---")
    st.subheader("📚 Recent Recipes")

    # Show first few recipes
    preview_count = min(3, len(recipes))
    st.markdown(f"Showing {preview_count} of {len(recipes)} recipes:")

    for recipe in recipes[:preview_count]:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**🍽️ {recipe.name}**")
                if recipe.step_times:
                    total_time = sum(recipe.step_times)
                    st.caption(f"{len(recipe.steps)} steps • ~{total_time} minutes")
                else:
                    st.caption(f"{len(recipe.steps)} steps • No timing info")

            with col2:
                if st.button("✏️ Edit", key=f"edit_{recipe.name}"):
                    st.switch_page("pages/📚_browse_recipes.py")

            with col3:
                if st.button("🍽️ Cook", key=f"cook_{recipe.name}"):
                    st.session_state.selected_recipes = [recipe.name]
                    st.switch_page("pages/🍽️_plan_meal.py")

    if len(recipes) > preview_count:
        st.markdown(f"... and {len(recipes) - preview_count} more recipes")
        if st.button("📋 Browse All Recipes"):
            st.switch_page("pages/📚_browse_recipes.py")
