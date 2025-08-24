#!/usr/bin/env python3
"""
Test Streamlit app for demonstrating step splitting functionality
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from meal_time.utils.step_splitter import StepSplitter
from meal_time.models.recipe import Recipe

st.set_page_config(page_title="Step Splitting Demo")

st.title("🔧 Recipe Step Splitting Demo")

st.markdown("""
This demo shows how the new step splitting functionality works.
Enter recipe steps that contain multiple time instructions, and see how they are automatically split.
""")

# Input section
st.subheader("Input Recipe Steps")

# Example steps
example_steps = [
    "Simmer for 10 minutes, then bake for 25 minutes",
    "Heat oil for 2 minutes, add onions and cook for 5 minutes, then add garlic and cook for 1 minute",
    "Preheat oven to 350°F. Bake for 30 minutes. Cool for 10 minutes before serving",
    "Mix ingredients for 2 minutes, let rest for 30 minutes, and bake for 45 minutes"
]

# Let user select an example or enter custom
option = st.radio("Choose input method:", ["Use example", "Enter custom steps"])

if option == "Use example":
    selected_example = st.selectbox("Select an example:", example_steps)
    steps_input = [selected_example]
else:
    steps_text = st.text_area(
        "Enter recipe steps (one per line):",
        placeholder="Mix flour and sugar for 2 minutes, then add eggs and beat for 1 minute\nBake for 25-30 minutes until golden\nCool for 10 minutes before serving",
        height=150
    )
    steps_input = [step.strip() for step in steps_text.split('\n') if step.strip()]

if st.button("Split Steps") and steps_input:
    st.subheader("Results")
    
    # Show original steps
    st.markdown("**Original Steps:**")
    for i, step in enumerate(steps_input, 1):
        st.write(f"{i}. {step}")
    
    # Split the steps
    new_steps, new_step_times = StepSplitter.split_recipe_steps(steps_input)
    
    st.markdown(f"**After Splitting ({len(steps_input)} → {len(new_steps)} steps):**")
    
    # Display split steps in a nice format
    for i, (step, time) in enumerate(zip(new_steps, new_step_times), 1):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{i}. {step}")
        with col2:
            st.metric("Time", f"{time} min")
    
    # Show time extraction analysis
    st.subheader("Time Extraction Analysis")
    
    total_time = sum(new_step_times)
    avg_time = total_time / len(new_step_times) if new_step_times else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Steps", len(new_steps))
    with col2:
        st.metric("Total Time", f"{total_time} min")
    with col3:
        st.metric("Avg Time/Step", f"{avg_time:.1f} min")
    
    # Show which steps had time extracted
    steps_with_time = sum(1 for time in new_step_times if time != 5)  # 5 is the default fallback
    extracted_times = [time for time in new_step_times if time != 5]
    
    if extracted_times:
        st.success(f"Successfully extracted times from {steps_with_time} steps: {extracted_times}")
    else:
        st.info("No specific times were extracted (using default 5-minute estimates)")

# Show information about the feature
st.subheader("How It Works")

st.markdown("""
The step splitting feature:

1. **Detects time patterns** like "10 minutes", "1 hour", "30 secs"
2. **Identifies conjunctions** like "then", "and", "next", "meanwhile"
3. **Splits complex steps** into simpler, individual steps
4. **Extracts timing** from each split step
5. **Cleans up text** with proper capitalization and punctuation

**Examples of patterns it handles:**
- "Cook for 10 minutes, then bake for 25 minutes"
- "Mix for 2 minutes. Let rest for 30 minutes. Bake for 45 minutes"
- "Heat oil for 1 minute, add garlic and cook for 30 seconds"
- "Simmer for 15-20 minutes until tender"
- "Bake for about 30 minutes until golden"
""")

# Test individual step splitting
st.subheader("Test Individual Step")
test_step = st.text_input("Enter a single step to test:", 
                         placeholder="Simmer for 10 minutes, then bake for 25 minutes")

if test_step:
    st.markdown("**Original:**")
    st.write(test_step)
    
    # Check if it needs splitting
    needs_splitting = StepSplitter.has_multiple_time_instructions(test_step)
    
    if needs_splitting:
        st.info("✅ This step contains multiple time instructions and will be split")
    else:
        st.info("ℹ️ This step does not need splitting")
    
    # Split the step
    split_results = StepSplitter.split_step(test_step)
    
    st.markdown("**Split Result:**")
    for i, result in enumerate(split_results, 1):
        time_str = f" ({result.time_minutes} min)" if result.time_minutes else " (no time)"
        st.write(f"{i}. {result.instruction}{time_str}")