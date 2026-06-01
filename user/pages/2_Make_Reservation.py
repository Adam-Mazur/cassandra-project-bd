import streamlit as st
import api
import random

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

movie_options = {m["title"]: str(m["movie_id"]) for m in movies}
cinema_options = {f"{c['name']} ({c['location']})": c for c in cinemas}

col1, col2 = st.columns(2)
with col1:
    selected_movie = st.selectbox("Movie", options=list(movie_options.keys()))
with col2:
    selected_cinema_label = st.selectbox("Cinema", options=list(cinema_options.keys()))

cinema = cinema_options[selected_cinema_label]
movie_id = movie_options[selected_movie]
cinema_id = str(cinema["cinema_id"])
capacity = cinema["capacity"]

# Per-showing selection state so changing movie/cinema resets selection
state_key = f"selected_seats_{movie_id}_{cinema_id}"
if state_key not in st.session_state:
    st.session_state[state_key] = set()

selected_seats: set = st.session_state[state_key]

try:
    all_reservations = api.get_reservations()
    occupied_seats = {
        r["seat_number"]
        for r in all_reservations
        if str(r["movie_id"]) == movie_id and str(r["cinema_id"]) == cinema_id
    }
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.stop()

selected_seats -= occupied_seats  # drop seats that got booked by someone else

# Style free (secondary) buttons green; selected = primary (blue); occupied = disabled (grey)
st.markdown("""
<style>
button[kind="secondary"]:not(:disabled) {
    background-color: #2ecc71 !important;
    border-color: #27ae60 !important;
    color: white !important;
    min-width: 44px !important;
    height: 44px !important;
    padding: 0 4px !important;
    font-size: 12px !important;
}
button[kind="secondary"]:not(:disabled):hover {
    background-color: #27ae60 !important;
    border-color: #219a52 !important;
}
button[kind="primary"] {
    background-color: #4169E1 !important;
    border-color: #3155c4 !important;
    color: white !important;
    min-width: 44px !important;
    height: 44px !important;
    padding: 0 4px !important;
    font-size: 12px !important;
}
button[kind="primary"]:hover {
    background-color: #3155c4 !important;
}
</style>
""", unsafe_allow_html=True)

free_count = capacity - len(occupied_seats)
st.markdown(
    f"**{capacity} seats** &nbsp;|&nbsp; "
    f"🟩 {free_count} free &nbsp; 🟦 {len(selected_seats)} selected &nbsp; ⬜ {len(occupied_seats)} occupied"
)

# Seat grid — 10 seats per row
COLS = 10
for row_start in range(0, capacity, COLS):
    cols = st.columns(COLS)
    for i, seat in enumerate(range(row_start + 1, min(row_start + COLS + 1, capacity + 1))):
        with cols[i]:
            if seat in occupied_seats:
                st.button(str(seat), key=f"seat_{seat}", disabled=True)
            elif seat in selected_seats:
                if st.button(str(seat), key=f"seat_{seat}", type="primary"):
                    selected_seats.discard(seat)
                    st.rerun()
            else:
                if st.button(str(seat), key=f"seat_{seat}"):
                    selected_seats.add(seat)
                    st.rerun()

if not selected_seats:
    st.stop()

st.divider()
st.write(f"Selected: **{sorted(selected_seats)}**")

if st.button("Confirm Reservation", type="primary", key="confirm"):
    try:
        result = api.make_reservations_bulk(
            user_id=user["user_id"],
            movie_id=movie_id,
            cinema_id=cinema_id,
            seat_numbers=sorted(selected_seats),
        )
        success = [r["seat_number"] for r in result["results"] if r["success"]]
        failed = [r["seat_number"] for r in result["results"] if not r["success"]]
    except (ConnectionError, RuntimeError) as e:
        st.error(str(e))
        st.stop()

    st.session_state[state_key] = set()

    if success:
        st.success(f"Reserved seats: {success}")
    if failed:
        st.warning(f"Already taken (skipped): {failed}")

    st.rerun()
