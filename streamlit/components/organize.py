import streamlit as st
from datetime import datetime, time, date, timedelta
from meal_time.services.recipe_service import RecipeService


def show(service: RecipeService):
    st.title("🍳 Organize Recipes for Cooking")

    recipes = service.list_recipes()
    if not recipes:
        st.info("No recipes found. Add some recipes first!")
        return

    # Initialize session state for persistence
    if 'selected_recipes' not in st.session_state:
        st.session_state.selected_recipes = []
    if 'target_date' not in st.session_state:
        st.session_state.target_date = date.today()
    if 'target_time' not in st.session_state:
        st.session_state.target_time = time(18, 0)  # 6 PM default

    # Recipe selection
    st.subheader("📋 Select Recipes")
    recipe_names = [r.name for r in recipes]
    selected = st.multiselect(
        "Choose recipes to cook together:",
        recipe_names,
        default=st.session_state.selected_recipes,  # Use saved state
        key="recipe_selector",
        help="Select multiple recipes to coordinate their timing"
    )

    # Update session state when selection changes
    st.session_state.selected_recipes = selected

    if not selected:
        st.info("👆 Select some recipes to get started!")
        return

    # Timing configuration with session state
    st.subheader("⏰ Set Your Target Time")

    col1, col2 = st.columns(2)
    with col1:
        target_date = st.date_input(
            "Date:",
            value=st.session_state.target_date,
            key="date_picker",
            help="When do you want to cook?"
        )
        st.session_state.target_date = target_date

    with col2:
        target_time_input = st.time_input(
            "Target completion time:",
            value=st.session_state.target_time,
            key="time_picker",
            help="When should all dishes be ready?"
        )
        st.session_state.target_time = target_time_input

    target_datetime = datetime.combine(target_date, target_time_input)

    # Time validation
    now = datetime.now()
    if target_datetime <= now:
        st.error(f"⏰ Target time must be in the future! Current time: {now.strftime('%H:%M')}")
        st.info("💡 Try setting your target time at least 30 minutes from now")
        return

    # Check if we have enough time to cook
    total_estimated_time = 0
    for recipe_name in selected:
        recipe = service.get_recipe_by_name(recipe_name)
        if recipe and recipe.total_time:
            total_estimated_time = max(total_estimated_time, recipe.total_time)

    time_available = (target_datetime - now).total_seconds() / 60  # minutes

    if total_estimated_time > time_available:
        st.warning(
            f"⚠️ Tight timing! You need ~{total_estimated_time} minutes but only have {time_available:.0f} minutes")
        st.info("💡 Consider moving your target time later, or the meal might be rushed")

        # Let them continue but with warning
        if not st.checkbox("⚡ Proceed anyway (rush mode)", key="rush_mode"):
            return

    # Generate the cooking plan
    try:
        steps = service.organize_recipes(selected, target_datetime)
        summary = service.get_cooking_summary(selected, target_datetime)

        if not steps:
            st.error("Could not organize recipes. Check that they have step times.")
            return

        # Check for past start times
        if steps:
            earliest_start = steps[0]["start_time"]
            if earliest_start <= now:
                st.error(
                    f"🚨 Impossible timing! You'd need to start cooking at {earliest_start.strftime('%H:%M')} (that's in the past!)")
                st.info("💡 Solutions:")
                st.info("   • Move your target time later")
                st.info("   • Choose simpler recipes")
                st.info("   • Start some prep work now")
                return

        # Show summary
        st.subheader("📊 Cooking Plan Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Time", f"{summary['total_time']} min")
        with col2:
            st.metric("Start At", summary['start_time'].strftime("%H:%M"))
        with col3:
            st.metric("Total Steps", summary['total_steps'])
        with col4:
            multitask = summary.get('multitask_opportunities', 0)
            st.metric("Multitask Steps", multitask)

        # Timeline view
        st.subheader("📅 Your Cooking Timeline")

        # Timeline display options
        view_mode = st.radio(
            "View mode:",
            ["Timeline", "Checklist", "Export"],
            horizontal=True
        )

        if view_mode == "Timeline":
            show_timeline_view(steps, target_datetime)
        elif view_mode == "Checklist":
            show_checklist_view(steps)
        else:  # Export
            show_export_view(service, selected, target_datetime)

        # Show ingredients summary
        show_ingredients_summary(service, selected)

    except Exception as e:
        st.error(f"Error organizing recipes: {str(e)}")
        st.info("Make sure your recipes have step times. You can regenerate them in the service.")


def show_timeline_view(steps, target_datetime):
    """Show steps organized by time"""
    st.info(f"🎯 All dishes will be ready at **{target_datetime.strftime('%H:%M')}**")

    current_time_group = None

    for step in steps:
        step_time = step["start_time"].strftime("%H:%M")

        # Show time header when time changes
        if step_time != current_time_group:
            st.markdown(f"### ⏰ {step_time}")
            current_time_group = step_time

        # Format step with color coding
        multitask_indicator = " 🔄" if step["can_multitask"] else ""
        prep_indicator = " 🔪" if step["is_prep"] else ""
        cooking_indicator = " 🔥" if step["is_cooking"] else ""

        step_text = f"{step['recipe_color']} **[{step['recipe_name']}]** {step['text']}"
        duration_text = f"*({step['duration']} min{multitask_indicator}{prep_indicator}{cooking_indicator})*"

        st.write(f"{step_text} {duration_text}")

        # Show gap to next step
        if step.get("time_gap", 0) > 0:
            st.write(f"   ⏸️ *{step['time_gap']:.0f} min break*")


def show_checklist_view(steps):
    """Show steps as an interactive checklist"""
    st.info("Check off steps as you complete them:")

    # Initialize session state for checkboxes
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = {}

    for i, step in enumerate(steps):
        step_key = f"step_{i}"
        step_time = step["start_time"].strftime("%H:%M")

        # Create checkbox for each step
        is_completed = st.checkbox(
            f"**{step_time}** - {step['recipe_color']} [{step['recipe_name']}] {step['text']} ({step['duration']} min)",
            key=step_key,
            value=st.session_state.completed_steps.get(step_key, False)
        )

        st.session_state.completed_steps[step_key] = is_completed

        if is_completed:
            st.success("✅ Completed!")

    # Progress tracking
    total_steps = len(steps)
    completed_count = sum(1 for completed in st.session_state.completed_steps.values() if completed)
    progress = completed_count / total_steps if total_steps > 0 else 0

    st.progress(progress)
    st.write(f"Progress: {completed_count}/{total_steps} steps completed ({progress:.1%})")


def show_export_view(service, selected, target_datetime):
    """Show export options"""
    st.subheader("📤 Export Your Timeline")

    # Generate text export
    timeline_text = service.export_cooking_timeline(selected, target_datetime)

    st.text_area(
        "Cooking Timeline (copy this!):",
        timeline_text,
        height=400,
        help="Copy this timeline to your notes app or print it out"
    )

    # Download button would go here in a real app
    st.info("💡 Tip: Copy the timeline above to your phone's notes app for easy reference while cooking!")


def show_ingredients_summary(service, selected):
    """Show consolidated ingredients list"""
    st.subheader("🛒 Shopping List")

    all_ingredients = []
    for recipe_name in selected:
        recipe = service.get_recipe_by_name(recipe_name)
        if recipe:
            st.write(f"**{recipe.name}:**")
            for ingredient in recipe.ingredients:
                st.write(f"• {ingredient}")
                all_ingredients.append(ingredient)

    if st.button("📋 Copy All Ingredients"):
        ingredients_text = "\n".join([f"• {ing}" for ing in all_ingredients])
        st.code(ingredients_text)
        st.info("Copy the ingredients above for your shopping list!")