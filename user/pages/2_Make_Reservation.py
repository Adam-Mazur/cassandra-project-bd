import streamlit as st
import api

st.set_page_config(page_title="Make Reservation", page_icon="🎟️", layout="wide")
st.title("Make a Reservation")

if not st.session_state.get("user"):
    st.warning("Please log in first via the Account page.")
    st.stop()

user = st.session_state["user"]
st.caption(f"Booking as: **{user['name']}**")

try:
    movies = api.get_movies()
    cinemas = api.get_cinemas()
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.stop()

if not movies:
    st.info("No movies available yet.")
    st.stop()

if not cinemas:
    st.info("No cinemas available yet.")
    st.stop()

movie_options = {m["title"]: m["movie_id"] for m in movies}
cinema_options = {f"{c['name']} ({c['location']})": c for c in cinemas}

selected_cinema_label = st.selectbox("Cinema", options=list(cinema_options.keys()))
cinema = cinema_options[selected_cinema_label]
st.caption(f"Capacity: **{cinema['capacity']}** seats")

with st.form("make_reservation"):
    selected_movie = st.selectbox("Movie", options=list(movie_options.keys()))
    seat_number = st.number_input(
        "Seat Number", min_value=1, max_value=cinema["capacity"], value=1
    )
    submitted = st.form_submit_button("Reserve", type="primary")

if submitted:
    try:
        result = api.make_reservation(
            user_id=user["user_id"],
            movie_id=movie_options[selected_movie],
            cinema_id=cinema["cinema_id"],
            seat_number=int(seat_number),
        )
        st.success(f"Reservation confirmed! ID: `{result['reservation_id']}`")
    except (ConnectionError, RuntimeError) as e:
        st.error(str(e))
