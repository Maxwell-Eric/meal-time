import streamlit as st
from meal_time.services.recipe_service import RecipeService

def show(service: RecipeService):
  st.title("Organize Recipes 🍳")

  recipes = service.list_recipes()
  if not recipes:
    st.info("No recipes found.")
    return

  recipe_names = [r.name for r in recipes]
  selected = st.multiselect("Select recipes to organize", recipe_names)

  if not selected:
    return

  st.subheader("Ingredients")
  for r in selected:
    recipe = service.get_recipe_by_name(r)
    if recipe:
      st.write(f"**{recipe.name}**")
      for ing in recipe.ingredients:
        st.write(f"- {ing}")

  st.subheader("Steps")
  steps = service.organize_recipes(selected)
  for i, step in enumerate(steps, start=1):
    st.write(f"{i}. [{step['recipe_name']}] {step['text']} (Estimated: {step['estimated_time']} min)")
