# pages/🔧_recipe_tools.py
import streamlit as st
from src.components.recipe_tools_components import show

st.set_page_config(
    page_title="Recipe Tools - Meal Time",
    page_icon="🔧",
    layout="wide"
)

# Get the recipe service from session state
if 'recipe_service' not in st.session_state:
    st.error("⚠️ Recipe service not initialized. Please go back to the home page first.")
    if st.button("🏠 Go to Home"):
        st.switch_page("app.py")
    st.stop()

service = st.session_state.recipe_service

# Use the recipe tools component
show(service)
