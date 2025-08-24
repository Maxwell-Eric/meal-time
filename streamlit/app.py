import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Import the organize page
from pages.organize import show as show_organize
from meal_time.services.recipe_service import RecipeService

st.set_page_config(page_title="Meal Time 🍴")

st.title("=== Meal Time 🍴 ===")

# Initialize recipe service
service = RecipeService()

# Sidebar for navigation
page = st.sidebar.selectbox(
    "Choose an option",
    ["Add a new recipe manually", "Add a new recipe from URL", "List recipes", "Organize recipes for cooking", "Exit"]
)

if page == "Add a new recipe manually":
    st.write("Add manual recipe page coming soon...")

elif page == "Add a new recipe from URL":
    st.write("Add recipe from URL page coming soon...")

elif page == "List recipes":
    if service.recipes:
        st.write("Recipes:")
        for r in service.recipes:
            st.write(f"- {r.name} | Prep: {r.prep_time} min | Cook: {r.cook_time} min | Total: {r.total_time} min")
    else:
        st.write("No recipes found.")

elif page == "Organize recipes for cooking":
    show_organize(service)

elif page == "Exit":
    st.write("Goodbye! 🍴")
