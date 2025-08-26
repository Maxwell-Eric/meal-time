import streamlit as st
from typing import List, Tuple
from src.meal_time_logic.models.recipe import Recipe
from src.meal_time_logic.services.step_time_parser_service import StepTimeParser, process_recipe_steps


def show_step_time_editor(recipe: Recipe) -> Tuple[List[str], List[int]]:
    """
    Show an interactive editor for recipe step times.
    Returns updated (steps, step_times) tuple.
    """
    st.subheader(f"⏱️ Step Times for: {recipe.name}")

    # Initialize parser
    parser = StepTimeParser()

    # Process the recipe steps to extract times
    if 'processed_steps' not in st.session_state:
        with st.spinner("Analyzing step times..."):
            expanded_steps, step_times, confidence_info = process_recipe_steps(recipe.steps)
            st.session_state.processed_steps = expanded_steps
            st.session_state.processed_times = step_times
            st.session_state.confidence_info = confidence_info

    expanded_steps = st.session_state.processed_steps
    step_times = st.session_state.processed_times
    confidence_info = st.session_state.confidence_info

    # Show summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Original Steps", len(recipe.steps))
    with col2:
        st.metric("Processed Steps", len(expanded_steps))
    with col3:
        total_time = sum(step_times)
        st.metric("Total Time", f"{total_time} min")
    with col4:
        extracted_count = sum(1 for c in confidence_info if c == 'extracted')
        st.metric("Times Found", f"{extracted_count}/{len(expanded_steps)}")

    # Show confidence breakdown
    confidence_counts = {}
    for conf in confidence_info:
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    st.info(f"📊 **Step Analysis**: "
            f"{confidence_counts.get('extracted', 0)} extracted, "
            f"{confidence_counts.get('predicted', 0)} predicted, "
            f"{confidence_counts.get('user_set', 0)} user-modified")

    # Mode selector
    mode = st.radio(
        "Choose editing mode:",
        ["Quick Review", "Detailed Editor", "Bulk Edit"],
        horizontal=True
    )

    if mode == "Quick Review":
        return show_quick_review(expanded_steps, step_times, confidence_info)
    elif mode == "Detailed Editor":
        return show_detailed_editor(expanded_steps, step_times, confidence_info, parser)
    else:  # Bulk Edit
        return show_bulk_editor(expanded_steps, step_times, confidence_info)


def show_quick_review(steps: List[str], times: List[int], confidence: List[str]) -> Tuple[List[str], List[int]]:
    """Show a quick overview with ability to adjust times"""
    st.markdown("### 👀 Quick Review")
    st.info("Review the automatically detected times. Click on any time to edit it.")

    updated_times = times.copy()

    for i, (step, time_val, conf) in enumerate(zip(steps, times, confidence)):
        with st.container():
            col1, col2, col3 = st.columns([6, 2, 1])

            with col1:
                # Color code by confidence
                if conf == 'extracted':
                    st.markdown(f"✅ **Step {i + 1}:** {step[:100]}{'...' if len(step) > 100 else ''}")
                elif conf == 'predicted':
                    st.markdown(f"🤖 **Step {i + 1}:** {step[:100]}{'...' if len(step) > 100 else ''}")
                else:
                    st.markdown(f"✏️ **Step {i + 1}:** {step[:100]}{'...' if len(step) > 100 else ''}")

            with col2:
                # Editable time
                new_time = st.number_input(
                    "minutes",
                    min_value=1,
                    max_value=300,
                    value=time_val,
                    key=f"quick_time_{i}",
                    label_visibility="collapsed"
                )
                if new_time != time_val:
                    updated_times[i] = new_time
                    confidence[i] = 'user_set'

            with col3:
                # Confidence indicator
                conf_emoji = {'extracted': '✅', 'predicted': '🤖', 'user_set': '✏️'}
                st.write(conf_emoji.get(conf, '?'))

    return steps, updated_times


def show_detailed_editor(steps: List[str], times: List[int], confidence: List[str], parser: StepTimeParser) -> Tuple[
    List[str], List[int]]:
    """Show detailed editor with step modification capabilities"""
    st.markdown("### ✏️ Detailed Editor")

    updated_steps = steps.copy()
    updated_times = times.copy()
    updated_confidence = confidence.copy()

    # Option to add new steps
    if st.button("➕ Add New Step"):
        new_step_text = st.text_input("New step text:", key="new_step_input")
        if new_step_text:
            suggestion = parser.suggest_step_time(new_step_text)
            new_time = st.number_input(
                f"Time for new step (suggested: {suggestion['time_minutes']} min):",
                min_value=1,
                value=suggestion['time_minutes'],
                key="new_step_time"
            )

            if st.button("Add Step"):
                updated_steps.append(new_step_text)
                updated_times.append(new_time)
                updated_confidence.append('user_set')
                st.success("Step added!")

    st.markdown("---")

    # Edit existing steps
    for i, (step, time_val, conf) in enumerate(zip(steps, times, confidence)):
        with st.expander(f"Step {i + 1} ({time_val} min) - {conf.title()}", expanded=False):

            # Edit step text
            new_step_text = st.text_area(
                "Step text:",
                value=step,
                key=f"step_text_{i}",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                # Edit time
                new_time = st.number_input(
                    "Time (minutes):",
                    min_value=1,
                    max_value=300,
                    value=time_val,
                    key=f"step_time_{i}"
                )

            with col2:
                # Re-analyze button
                if st.button(f"🔍 Re-analyze", key=f"reanalyze_{i}"):
                    suggestion = parser.suggest_step_time(new_step_text)
                    st.info(f"Suggested time: {suggestion['time_minutes']} min "
                            f"(confidence: {suggestion['confidence']})")
                    if suggestion['phrases_found']:
                        st.info(f"Found phrases: {', '.join(suggestion['phrases_found'])}")

            # Update if changed
            if new_step_text != step:
                updated_steps[i] = new_step_text
                updated_confidence[i] = 'user_set'

            if new_time != time_val:
                updated_times[i] = new_time
                updated_confidence[i] = 'user_set'

            # Delete button
            if st.button(f"🗑️ Delete Step {i + 1}", key=f"delete_{i}"):
                # Mark for deletion (we'll handle this outside the loop)
                st.session_state[f"delete_step_{i}"] = True

    # Handle deletions (outside the loop to avoid index issues)
    steps_to_delete = []
    for i in range(len(steps)):
        if st.session_state.get(f"delete_step_{i}", False):
            steps_to_delete.append(i)
            st.session_state[f"delete_step_{i}"] = False

    # Remove deleted steps (in reverse order to maintain indices)
    for i in sorted(steps_to_delete, reverse=True):
        updated_steps.pop(i)
        updated_times.pop(i)
        updated_confidence.pop(i)

    if steps_to_delete:
        st.success(f"Deleted {len(steps_to_delete)} step(s)")

    return updated_steps, updated_times


def show_bulk_editor(steps: List[str], times: List[int], confidence: List[str]) -> Tuple[List[str], List[int]]:
    """Show bulk editing options"""
    st.markdown("### 📊 Bulk Editor")

    updated_times = times.copy()

    # Bulk operations
    st.markdown("**Bulk Operations:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⚡ Quick Times"):
            # Set common quick times
            for i in range(len(updated_times)):
                if 'mix' in steps[i].lower() or 'stir' in steps[i].lower():
                    updated_times[i] = 2
                elif 'chop' in steps[i].lower() or 'dice' in steps[i].lower():
                    updated_times[i] = 5
                elif 'cook' in steps[i].lower():
                    updated_times[i] = 15
            st.success("Applied quick time estimates!")

    with col2:
        multiplier = st.number_input("Scale all times by:", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
        if st.button("🔢 Scale Times"):
            updated_times = [max(1, int(time * multiplier)) for time in updated_times]
            st.success(f"Scaled all times by {multiplier}x")

    with col3:
        min_time = st.number_input("Set minimum time:", min_value=1, max_value=60, value=1)
        if st.button("⬆️ Set Minimums"):
            updated_times = [max(min_time, time) for time in updated_times]
            st.success(f"Set minimum time to {min_time} minutes")

    # Show bulk editor table
    st.markdown("**Edit Multiple Steps:**")

    # Create editable dataframe
    import pandas as pd

    df_data = {
        'Step': [f"{i + 1}: {step[:50]}{'...' if len(step) > 50 else ''}" for i, step in enumerate(steps)],
        'Minutes': updated_times,
        'Confidence': confidence
    }

    df = pd.DataFrame(df_data)
    edited_df = st.data_editor(
        df,
        column_config={
            "Minutes": st.column_config.NumberColumn(
                "Minutes",
                min_value=1,
                max_value=300,
            )
        },
        hide_index=True,
        use_container_width=True
    )

    # Update times from edited dataframe
    updated_times = edited_df['Minutes'].tolist()

    return steps, updated_times


def show_step_timing_help():
    """Show help information about step timing"""
    with st.expander("❓ How Step Timing Works", expanded=False):
        st.markdown("""
        **🔍 Automatic Detection:**
        - Finds explicit times: "cook for 10 minutes", "bake 1 hour"
        - Handles ranges: "simmer 10-15 minutes" 
        - Recognizes fractions: "rest for ½ hour"

        **🤖 Smart Predictions:**
        - Uses machine learning for steps without times
        - Based on cooking action keywords
        - Learns from your corrections over time

        **✏️ Manual Override:**
        - You can always edit any time
        - Changes are remembered for similar steps
        - Bulk edit tools for efficiency

        **📊 Confidence Levels:**
        - ✅ **Extracted**: Found explicit time in text
        - 🤖 **Predicted**: ML estimated based on step content  
        - ✏️ **User Set**: You manually adjusted the time
        """)
