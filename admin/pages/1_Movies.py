import streamlit as st
import api

st.set_page_config(page_title="Movies", page_icon="🎬", layout="wide")
st.title("Movies")

with st.form("create_movie"):
    st.subheader("Add Movie")
    col1, col2 = st.columns([3, 1])
    title = col1.text_input("Title")
    duration = col2.number_input("Duration (min)", min_value=1, value=90)
    submitted = st.form_submit_button("Add Movie", type="primary")

if submitted:
    if not title.strip():
        st.error("Title cannot be empty.")
    else:
        try:
            api.create_movie(title.strip(), duration)
            st.success(f"Movie '{title}' added.")
        except (ConnectionError, RuntimeError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Failed to add movie: {e}")

st.divider()
st.subheader("All Movies")

try:
    movies = api.get_movies()
    if movies:
        st.dataframe(movies, use_container_width=True)
    else:
        st.info("No movies yet.")
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
