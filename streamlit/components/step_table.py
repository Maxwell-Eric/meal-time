import streamlit as st


def show_steps(recipe):
    st.markdown(f"### {recipe.name}")
    for i, (step, time) in enumerate(zip(recipe.steps, recipe.step_times), start=1):
        st.write(f"{i}. [{time} min] {step}")
