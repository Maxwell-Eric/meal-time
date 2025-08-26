# streamlit/components/recipe_editor.py
import streamlit as st
from src.meal_time_logic.models.recipe import Recipe


def show_recipe_editor(service, recipe: Recipe):
    """Show inline recipe editor"""
    st.markdown(f"### ✏️ Editing: {recipe.name}")

    # Tabs for different aspects
    tab1, tab2, tab3 = st.tabs(["📝 Basic Info", "🧾 Ingredients", "👨‍🍳 Steps"])

    with tab1:
        show_basic_info_editor(service, recipe)

    with tab2:
        show_ingredients_editor(service, recipe)

    with tab3:
        show_steps_editor(service, recipe)


def show_basic_info_editor(service, recipe: Recipe):
    """Edit basic recipe information"""
    with st.form(f"basic_info_{recipe.name}"):
        # Recipe name
        new_name = st.text_input("Recipe Name:", value=recipe.name)

        # Time information
        col1, col2, col3 = st.columns(3)
        with col1:
            new_prep_time = st.number_input(
                "Prep Time (min):",
                min_value=0,
                value=recipe.prep_time or 0
            )
        with col2:
            new_cook_time = st.number_input(
                "Cook Time (min):",
                min_value=0,
                value=recipe.cook_time or 0
            )
        with col3:
            suggested_total = sum(recipe.step_times) if recipe.step_times else 0
            new_total_time = st.number_input(
                f"Total Time (min) [Auto: {suggested_total}]:",
                min_value=0,
                value=recipe.total_time or suggested_total
            )

        if st.form_submit_button("💾 Update Basic Info"):
            updated_recipe = Recipe(
                name=new_name,
                ingredients=recipe.ingredients,
                steps=recipe.steps,
                prep_time=new_prep_time if new_prep_time > 0 else None,
                cook_time=new_cook_time if new_cook_time > 0 else None,
                total_time=new_total_time if new_total_time > 0 else None,
                step_times=recipe.step_times
            )

            try:
                service.update_recipe(updated_recipe)
                st.success("✅ Basic info updated!")
            except Exception as e:
                st.error(f"Error: {e}")


def show_ingredients_editor(service, recipe: Recipe):
    """Edit recipe ingredients"""
    st.markdown("**Current Ingredients:**")

    # Initialize session state for ingredients if not exists
    if f"ingredients_{recipe.name}" not in st.session_state:
        st.session_state[f"ingredients_{recipe.name}"] = recipe.ingredients.copy()

    # Editable ingredients list
    ingredients_list = st.session_state[f"ingredients_{recipe.name}"]

    for i, ingredient in enumerate(ingredients_list):
        col1, col2 = st.columns([5, 1])
        with col1:
            updated = st.text_input(
                f"Ingredient {i + 1}:",
                value=ingredient,
                key=f"ing_{recipe.name}_{i}_{len(ingredients_list)}"  # Add length to make key unique
            )
            # Update the ingredient in session state
            st.session_state[f"ingredients_{recipe.name}"][i] = updated.strip()
        with col2:
            # Make the trashcan clickable
            if st.button("🗑️", key=f"delete_{recipe.name}_{i}_{len(ingredients_list)}"):
                st.session_state[f"ingredients_{recipe.name}"].pop(i)
                st.rerun()

    # Add new ingredient
    st.markdown("**Add New:**")
    new_ingredient = st.text_input("New ingredient:", key=f"new_ing_{recipe.name}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Ingredient") and new_ingredient.strip():
            st.session_state[f"ingredients_{recipe.name}"].append(new_ingredient.strip())
            st.rerun()

    with col2:
        if st.button("💾 Save Ingredients"):
            # Filter out empty ingredients
            final_ingredients = [ing for ing in st.session_state[f"ingredients_{recipe.name}"] if ing.strip()]

            updated_recipe = Recipe(
                name=recipe.name,
                ingredients=final_ingredients,
                steps=recipe.steps,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                total_time=recipe.total_time,
                step_times=recipe.step_times
            )

            try:
                service.update_recipe(updated_recipe)
                st.success("✅ Ingredients updated!")
                # Update the session state to reflect the saved changes
                st.session_state[f"ingredients_{recipe.name}"] = final_ingredients.copy()
            except Exception as e:
                st.error(f"Error: {e}")


def show_steps_editor(service, recipe: Recipe):
    """Edit recipe steps and times"""
    st.markdown("**Recipe Steps:**")

    # Show current step times status
    if recipe.step_times and len(recipe.step_times) == len(recipe.steps):
        total_time = sum(recipe.step_times)
        st.info(f"⏱️ Total time: {total_time} minutes ({len(recipe.steps)} steps)")
    else:
        st.warning("⚠️ Step times missing or incomplete")

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Auto-Generate Times"):
            with st.spinner("Analyzing steps..."):
                try:
                    enhanced = service.process_recipe_step_times(recipe)
                    service.update_recipe(enhanced)
                    st.success("✅ Generated step times!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("📊 Analyze Steps"):
            try:
                analysis = service.get_step_time_analysis(recipe)
                show_step_analysis(analysis)
            except Exception as e:
                st.error(f"Error: {e}")

    # Edit steps
    new_steps = []
    new_times = []

    for i, step in enumerate(recipe.steps):
        st.markdown(f"**Step {i + 1}:**")

        col1, col2 = st.columns([4, 1])
        with col1:
            updated_step = st.text_area(
                f"Step {i + 1} text:",
                value=step,
                key=f"step_{recipe.name}_{i}",
                height=100,
                label_visibility="collapsed"
            )
            if updated_step.strip():
                new_steps.append(updated_step.strip())

        with col2:
            current_time = recipe.step_times[i] if recipe.step_times and i < len(recipe.step_times) else 5
            updated_time = st.number_input(
                f"Minutes:",
                min_value=1,
                max_value=300,
                value=current_time,
                key=f"time_{recipe.name}_{i}",
                label_visibility="collapsed"
            )
            new_times.append(updated_time)

    # Add new step
    st.markdown("**Add New Step:**")
    new_step_text = st.text_area("New step:", key=f"new_step_{recipe.name}")
    new_step_time = st.number_input("Time (min):", min_value=1, value=5, key=f"new_time_{recipe.name}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Step") and new_step_text.strip():
            new_steps.append(new_step_text.strip())
            new_times.append(new_step_time)

    with col2:
        if st.button("💾 Save All Steps"):
            updated_recipe = Recipe(
                name=recipe.name,
                ingredients=recipe.ingredients,
                steps=new_steps,
                prep_time=recipe.prep_time,
                cook_time=recipe.cook_time,
                total_time=sum(new_times) if new_times else recipe.total_time,
                step_times=new_times
            )

            try:
                service.update_recipe(updated_recipe)
                st.success("✅ Steps updated!")
            except Exception as e:
                st.error(f"Error: {e}")


def show_step_analysis(analysis):
    """Show step timing analysis"""
    st.markdown("### 📊 Step Analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Steps", analysis['processed_steps'])
    with col2:
        st.metric("Times Found", analysis['extracted_times'])
    with col3:
        st.metric("Total Time", f"{analysis['total_time_minutes']} min")

    if analysis['needs_review']:
        st.warning(f"⚠️ {len(analysis['needs_review'])} steps need review:")
        for issue in analysis['needs_review']:
            st.write(f"• Step {issue['step_number']}: {issue['reason']}")


def show_manual_recipe_form(service):
    """Show form to add a recipe manually"""
    st.markdown("Add a new recipe by filling out the form below:")

    with st.form("add_recipe_form"):
        # Basic info
        recipe_name = st.text_input("Recipe Name*:", placeholder="e.g., Chocolate Chip Cookies")

        col1, col2 = st.columns(2)
        with col1:
            prep_time = st.number_input("Prep Time (minutes):", min_value=0, value=15)
        with col2:
            cook_time = st.number_input("Cook Time (minutes):", min_value=0, value=30)

        # Ingredients
        st.markdown("**Ingredients:**")
        ingredients_text = st.text_area(
            "Enter ingredients (one per line):",
            placeholder="2 cups flour\n1 cup sugar\n2 eggs\n...",
            height=150
        )

        # Steps
        st.markdown("**Instructions:**")
        steps_text = st.text_area(
            "Enter cooking steps (one per line):",
            placeholder="Preheat oven to 350°F\nMix dry ingredients in a bowl\nAdd wet ingredients and stir\nBake for 15 minutes\n...",
            height=200
        )

        submitted = st.form_submit_button("➕ Add Recipe", type="primary")

        if submitted:
            if not recipe_name.strip():
                st.error("Recipe name is required!")
                return

            if not ingredients_text.strip():
                st.error("At least one ingredient is required!")
                return

            if not steps_text.strip():
                st.error("At least one step is required!")
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
                total_time=(prep_time + cook_time) if (prep_time + cook_time) > 0 else None,
                step_times=[]
            )

            try:
                # Use the service method that processes step times automatically
                processed_recipe = service.add_recipe_with_time_processing(new_recipe)
                st.success(f"✅ Successfully added '{recipe_name}'!")
                st.success(f"🤖 Generated step times automatically!")

                # Show the added recipe
                with st.expander(f"Preview: {processed_recipe.name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Ingredients", len(processed_recipe.ingredients))
                    with col2:
                        st.metric("Steps", len(processed_recipe.steps))
                    with col3:
                        if processed_recipe.step_times:
                            total = sum(processed_recipe.step_times)
                            st.metric("Est. Time", f"{total} min")

                # Clear the form by rerunning
                st.rerun()

            except Exception as e:
                st.error(f"Error adding recipe: {e}")
