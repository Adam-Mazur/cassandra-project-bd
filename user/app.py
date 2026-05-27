import streamlit as st

st.set_page_config(page_title="Cinema", page_icon="🎬", layout="wide")
st.title("Welcome to Cinema Reservations")

if st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(f"Logged in as **{user['name']}**")
    st.write("Use the sidebar to browse movies, make reservations, or manage your bookings.")
else:
    st.info("Go to **Account** in the sidebar to log in or create an account.")
