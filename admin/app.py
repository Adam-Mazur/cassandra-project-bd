import streamlit as st
import api

st.set_page_config(page_title="Cinema Admin", page_icon="🎬", layout="wide")

st.title("Cinema Admin Panel")
st.caption("Use the sidebar to navigate between sections.")

st.divider()

try:
    movies = api.get_movies()
    cinemas = api.get_cinemas()
    users = api.get_users()
    reservations = api.get_reservations()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Movies", len(movies))
    col2.metric("Cinemas", len(cinemas))
    col3.metric("Users", len(users))
    col4.metric("Active Reservations", len(reservations))

except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.info("Make sure the FastAPI backend is running: `uv run fastapi dev src/main.py`")
