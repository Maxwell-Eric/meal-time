# import_web.py
import streamlit as st
from meal_time.services.recipe_service import RecipeService


def show(service: RecipeService):
    st.title("🌐 Import Recipe from Web")

    st.markdown("""
    Import recipes directly from cooking websites! Just paste a URL and we'll try to extract:
    - Recipe name and ingredients
    - Step-by-step instructions
    - Timing information (if available)

    **Works best with popular recipe sites like:**
    - AllRecipes, Food Network, Bon Appétit
    - Personal cooking blogs
    - Sites with structured recipe data
    """)

    # URL input
    url = st.text_input(
        "Recipe URL:",
        placeholder="https://www.example.com/amazing-recipe",
        help="Paste the full URL of the recipe page"
    )

    if not url:
        st.info("👆 Enter a recipe URL to get started!")
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🔍 Preview Recipe", use_container_width=True):
            with st.spinner("Scraping recipe..."):
                result = service.preview_recipe_from_url(url)
                st.session_state.preview_result = result

    with col2:
        if st.button("⬇️ Import Recipe", use_container_width=True):
            with st.spinner("Importing recipe..."):
                result = service.import_recipe_from_url(url)
                st.session_state.import_result = result

    # Show preview results
    if hasattr(st.session_state, 'preview_result'):
        show_preview_result(st.session_state.preview_result)

    # Show import results
    if hasattr(st.session_state, 'import_result'):
        show_import_result(st.session_state.import_result)


def show_preview_result(result):
    """Display preview results"""
    st.subheader("📋 Recipe Preview")

    if not result['success']:
        st.error(f"❌ Could not scrape recipe: {result['error']}")

        st.markdown("**Troubleshooting tips:**")
        st.info("• Make sure the URL is correct and accessible")
        st.info("• Check that the site is supported by recipe-scrapers")
        st.info("• Try a different recipe URL")
        st.info("• Some recipe sites may not be supported")
        return

    recipe = result['recipe']
    issues = result.get('validation_issues', [])

    st.success(f"✅ Recipe scraped successfully!")

    # Show validation issues
    if issues:
        st.warning("⚠️ **Validation Issues Found:**")
        for issue in issues:
            st.write(f"• {issue}")

    # Show recipe details
    st.markdown("---")

    st.subheader(f"📝 {recipe.name}")

    # Recipe stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ingredients", len(recipe.ingredients))
    with col2:
        st.metric("Steps", len(recipe.steps))
    with col3:
        if recipe.prep_time:
            st.metric("Prep Time", f"{recipe.prep_time} min")
    with col4:
        if recipe.cook_time:
            st.metric("Cook Time", f"{recipe.cook_time} min")

    # Ingredients
    st.markdown("**🥬 Ingredients:**")
    if recipe.ingredients:
        for ingredient in recipe.ingredients:
            st.write(f"• {ingredient}")
    else:
        st.write("*No ingredients found*")

    # Steps
    st.markdown("**👨‍🍳 Instructions:**")
    if recipe.steps:
        for i, step in enumerate(recipe.steps, 1):
            with st.expander(
                    f"Step {i} ({recipe.step_times[i - 1] if recipe.step_times and i <= len(recipe.step_times) else '?'} min)"):
                st.write(step)
    else:
        st.write("*No instructions found*")

    # Show predicted step times
    if recipe.step_times:
        total_time = sum(recipe.step_times)
        st.markdown(f"**⏰ Estimated Cooking Time:** {total_time} minutes")
        with st.expander("Step-by-step timing"):
            for i, (step, time) in enumerate(zip(recipe.steps, recipe.step_times), 1):
                st.write(f"{i}. **{time} min:** {step[:100]}{'...' if len(step) > 100 else ''}")


def show_import_result(result):
    """Display import results"""
    st.subheader("📥 Import Results")

    if not result['success']:
        st.error(f"❌ Import failed: {result['error']}")
        return

    recipe = result['recipe']
    issues = result.get('validation_issues', [])
    name_changed = result.get('name_changed', False)

    st.success("✅ Recipe imported successfully!")

    if name_changed:
        st.info(f"ℹ️ Recipe name was modified to avoid duplicates: **{recipe.name}**")

    # Show final recipe summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Ingredients", len(recipe.ingredients))
    with col2:
        st.metric("Steps", len(recipe.steps))
    with col3:
        st.metric("Step Times", len(recipe.step_times))
    with col4:
        if recipe.total_time:
            st.metric("Total Time", f"{recipe.total_time} min")
        else:
            estimated_time = sum(recipe.step_times) if recipe.step_times else 0
            st.metric("Est. Time", f"{estimated_time} min")

    # Show any validation issues
    if issues:
        with st.expander("⚠️ Validation Issues", expanded=False):
            for issue in issues:
                st.write(f"• {issue}")
            st.info("You can edit the recipe later to fix these issues.")

    st.success(f"🎉 **{recipe.name}** has been added to your recipe collection!")

    # Clear the session state
    if st.button("🆕 Import Another Recipe"):
        if 'preview_result' in st.session_state:
            del st.session_state.preview_result
        if 'import_result' in st.session_state:
            del st.session_state.import_result
        st.rerun()


def show_import_tips():
    """Show helpful tips for importing"""
    with st.expander("💡 Tips for Better Imports", expanded=False):
        st.markdown("""
        **For best results:**

        🎯 **Use recipe-focused URLs** - Direct links to recipe pages work better than homepage URLs

        🏷️ **Popular sites work best** - Sites with proper recipe markup (JSON-LD, microdata) give better results

        📱 **Try the desktop version** - Some mobile recipe pages have less structured data

        🔄 **Preview first** - Use "Preview" to check quality before importing

        ✏️ **Edit after import** - You can always edit recipes after importing to fix any issues

        **If scraping fails:**
        - Check that the URL is accessible in your browser
        - Some sites block automated requests
        - Try copying the recipe manually using "Add Recipe" instead
        """)


if __name__ == "__main__":
    show_import_tips()
