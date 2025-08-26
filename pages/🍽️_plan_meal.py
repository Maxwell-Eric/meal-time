# pages/🍽️_plan_meal.py
import streamlit as st
from src.components.organize import show

st.set_page_config(
    page_title="Plan Meal - Meal Time",
    page_icon="🍽️",
    layout="wide"
)

# Get the recipe service from session state
if 'recipe_service' not in st.session_state:
    st.error("⚠️ Recipe service not initialized. Please go back to the home page first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("app.py")
    st.stop()

service = st.session_state.recipe_service

# Use the organize component
show(service)
