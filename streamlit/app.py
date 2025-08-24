import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import the organize page and web import page
from components.organize import show as show_organize
from components.import_recipe_from_web import show as show_web_import
from meal_time.services.recipe_service import RecipeService

st.set_page_config(page_title="Meal Time 🍴")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap');
    </style>
    """,
    unsafe_allow_html=True
)

# st.title("=== Meal Time 🍴 ===")

st.markdown(
    """
    <h1 style="font-family: 'Arial', sans-serif; font-size: 36px; text-align: center;">
        🍴 Meal Time by<span style="font-family: 'Great Vibes', cursive; font-size: 52px; color: #b56576;">
        Paige
        </span> 🍴
    </h1>
    """,
    unsafe_allow_html=True
)

# Initialize recipe service
try:
    service = RecipeService()
except Exception as e:
    st.error(f"Error initializing recipe service: {e}")
    st.info("Make sure you have the required data directory and files set up.")
    st.stop()

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Choose an option",
    [
        "Add a new recipe manually",
        "🌐 Add a new recipe from URL",
        "List recipes",
        "🍽️ Plan a Meal (Coordinate Recipes)",
        "Exit"
    ]
)

if page == "Add a new recipe manually":
    st.write("Add manual recipe page coming soon...")
    # TODO: Create components/add_recipe_manual.py

elif page == "🌐 Add a new recipe from URL":
    # Use the existing web import component
    try:
        show_web_import(service)
    except Exception as e:
        st.error(f"Error loading web import: {e}")
        st.info("Make sure you have recipe-scrapers installed: `pip install recipe-scrapers`")

elif page == "List recipes":
    st.subheader("📚 Your Recipe Collection")

    if service.recipes:
        st.write(f"**Total recipes: {len(service.recipes)}**")

        # Add search functionality
        search = st.text_input("🔍 Search recipes:", placeholder="Type recipe name...")

        filtered_recipes = service.recipes
        if search:
            filtered_recipes = [r for r in service.recipes
                                if search.lower() in r.name.lower()]

        if filtered_recipes:
            for r in filtered_recipes:
                with st.expander(f"📄 {r.name}"):
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Ingredients", len(r.ingredients))
                    with col2:
                        st.metric("Steps", len(r.steps))
                    with col3:
                        if r.prep_time:
                            st.metric("Prep Time", f"{r.prep_time} min")
                        else:
                            st.write("Prep Time: Unknown")
                    with col4:
                        if r.cook_time:
                            st.metric("Cook Time", f"{r.cook_time} min")
                        else:
                            st.write("Cook Time: Unknown")

                    # Show step times if available
                    if r.step_times and len(r.step_times) == len(r.steps):
                        total_time = sum(r.step_times)
                        st.write(f"**Total estimated time:** {total_time} minutes")

                    # Show ingredients
                    st.markdown("**Ingredients:**")
                    for ingredient in r.ingredients[:5]:  # Show first 5
                        st.write(f"• {ingredient}")
                    if len(r.ingredients) > 5:
                        st.write(f"... and {len(r.ingredients) - 5} more")

                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Edit {r.name}", key=f"edit_{r.name}"):
                            st.info("Recipe editing coming soon!")
                    with col2:
                        if st.button(f"Delete {r.name}", key=f"delete_{r.name}"):
                            if st.button(f"Confirm delete {r.name}?", key=f"confirm_{r.name}"):
                                try:
                                    service.delete_recipe(r.name)
                                    st.success(f"Deleted {r.name}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting recipe: {e}")
        else:
            st.info("No recipes found matching your search.")
    else:
        st.info("No recipes found. Add some recipes first!")
        st.markdown("**Get started by:**")
        st.write("• Adding a recipe from a website URL")
        st.write("• Manually entering a recipe")

elif page == "🍽️ Plan a Meal (Coordinate Recipes)":
    show_organize(service)

elif page == "Exit":
    st.write("Thanks for using Meal Time! 🍴")
    st.balloons()
