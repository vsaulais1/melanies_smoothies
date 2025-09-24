# streamlit_app.py

# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
from snowflake.snowpark import Row

st.set_page_config(page_title="Customise your Smoothie", page_icon="🥤")

# Title & intro
st.title(":cup_with_straw: Customise your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!"""
)

# Name input
name_on_order = st.text_input("Name on Smoothie")
if name_on_order:
    st.write("The name on your smoothie will be", name_on_order)

# --- Get a Snowpark session (works in Snowflake & locally/Cloud) ---
def get_session():
    try:
        # Works in Snowflake Native App / Snowflake-hosted Streamlit
        return get_active_session()
    except Exception:
        # Works in Streamlit (local or Cloud) with a configured Snowflake connection
        # Add a [connections.snowflake] block in .streamlit/secrets.toml
        cnx = st.connection("snowflake")
        return cnx.session()

session = get_session()

# --- Load fruit options ---
fruit_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
    .select(col("FRUIT_NAME"))
    .sort(col("FRUIT_NAME"))
)

# Convert to Python list for the multiselect
fruit_options = [r["FRUIT_NAME"] for r in fruit_df.collect()]

# Optional preview
# st.dataframe(fruit_df.to_pandas(), use_container_width=True)

# --- Ingredient picker ---
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients",
    options=fruit_options,
    max_selections=5,
)

# --- Submit order ---
submit_col, _ = st.columns([1, 3])
with submit_col:
    time_to_insert = st.button("Submit Order", type="primary", disabled=not ingredients_list or not name_on_order)

# Build a clean ingredients string for display
ingredients_string = " ".join(ingredients_list) if ingredients_list else ""

if time_to_insert:
    if not name_on_order:
        st.error("Please enter a name for the smoothie.")
    elif not ingredients_list:
        st.error("Please choose at least one ingredient.")
    else:
        # Safe write using Snowpark DataFrame (no raw SQL concatenation)
        order_rows = [Row(INGREDIENTS=ingredients_string, NAME_ON_ORDER=name_on_order)]
        session.create_dataframe(order_rows).write.save_as_table(
            "SMOOTHIES.PUBLIC.ORDERS", mode="append"
        )

        st.success(f"Your Smoothie is ordered, {name_on_order}! ✅")
        st.caption(f"Ingredients: {ingredients_string}")

        # (Optional) Show the last order inserted
        # last_order = session.sql(
        #     "select * from SMOOTHIES.PUBLIC.ORDERS order by created_at desc limit 1"
        # ).to_pandas()
        # st.dataframe(last_order, use_container_width=True)
