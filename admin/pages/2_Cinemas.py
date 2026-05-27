import streamlit as st
import api

st.set_page_config(page_title="Cinemas", page_icon="🏛️", layout="wide")
st.title("Cinemas")

with st.form("create_cinema"):
    st.subheader("Add Cinema")
    col1, col2, col3 = st.columns([2, 2, 1])
    name = col1.text_input("Name")
    location = col2.text_input("Location")
    capacity = col3.number_input("Capacity", min_value=1, value=100)
    submitted = st.form_submit_button("Add Cinema", type="primary")

if submitted:
    if not name.strip():
        st.error("Name cannot be empty.")
    elif not location.strip():
        st.error("Location cannot be empty.")
    else:
        try:
            api.create_cinema(name.strip(), location.strip(), capacity)
            st.success(f"Cinema '{name}' added.")
        except (ConnectionError, RuntimeError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Failed to add cinema: {e}")

st.divider()
st.subheader("All Cinemas")

try:
    cinemas = api.get_cinemas()
    if cinemas:
        st.dataframe(cinemas, use_container_width=True)
    else:
        st.info("No cinemas yet.")
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
