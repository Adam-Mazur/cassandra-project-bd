import streamlit as st
import api

st.set_page_config(page_title="My Reservations", page_icon="🎟️", layout="wide")
st.title("My Reservations")

if not st.session_state.get("user"):
    st.warning("Please log in first via the Account page.")
    st.stop()

user = st.session_state["user"]

try:
    movies = api.get_movies()
    cinemas = api.get_cinemas()
    all_reservations = api.get_reservations()
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.stop()

if not movies or not cinemas:
    st.info("No movies or cinemas available yet.")
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

# Build seat maps for this showing
my_seats: dict[int, str] = {}   # seat_number -> reservation_id
other_occupied: set[int] = set()

for r in all_reservations:
    if str(r["movie_id"]) == movie_id and str(r["cinema_id"]) == cinema_id:
        if str(r["user_id"]) == str(user["user_id"]):
            my_seats[r["seat_number"]] = str(r["reservation_id"])
        else:
            other_occupied.add(r["seat_number"])

if not my_seats:
    st.info("You have no reservations for this showing.")
    st.stop()

# Per-showing cancellation selection state
state_key = f"cancel_seats_{movie_id}_{cinema_id}"
if state_key not in st.session_state:
    st.session_state[state_key] = set()

cancel_seats: set = st.session_state[state_key]
cancel_seats &= set(my_seats.keys())  # drop any that no longer exist

# CSS:  my seats (primary) = blue,  selected for cancel (secondary active) = red
st.markdown("""
<style>
button[kind="primary"] {
    background-color: #4169E1 !important;
    border-color: #3155c4 !important;
    color: white !important;
    min-width: 44px !important;
    height: 44px !important;
    padding: 0 4px !important;
    font-size: 12px !important;
}
button[kind="primary"]:hover { background-color: #3155c4 !important; }
button[kind="secondary"]:not(:disabled) {
    background-color: #e74c3c !important;
    border-color: #c0392b !important;
    color: white !important;
    min-width: 44px !important;
    height: 44px !important;
    padding: 0 4px !important;
    font-size: 12px !important;
}
button[kind="secondary"]:not(:disabled):hover { background-color: #c0392b !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"🟦 {len(my_seats)} my seats &nbsp;|&nbsp; "
    f"🟥 {len(cancel_seats)} selected for cancel &nbsp;|&nbsp; "
    f"⬜ {len(other_occupied)} others"
)

COLS = 10
for row_start in range(0, capacity, COLS):
    cols = st.columns(COLS)
    for i, seat in enumerate(range(row_start + 1, min(row_start + COLS + 1, capacity + 1))):
        with cols[i]:
            if seat not in my_seats:
                # free or someone else's seat — grey, non-interactive
                st.button(str(seat), key=f"seat_{seat}", disabled=True)
            elif seat in cancel_seats:
                # selected for cancel — red (secondary)
                if st.button(str(seat), key=f"seat_{seat}"):
                    cancel_seats.discard(seat)
                    st.rerun()
            else:
                # my seat, not selected — blue (primary)
                if st.button(str(seat), key=f"seat_{seat}", type="primary"):
                    cancel_seats.add(seat)
                    st.rerun()

if cancel_seats:
    st.divider()
    st.write(f"Cancel seats: **{sorted(cancel_seats)}**")
    if st.button("Confirm Cancellation", type="primary", key="confirm_cancel"):
        reservation_ids = [my_seats[seat] for seat in cancel_seats]
        try:
            api.cancel_reservations(reservation_ids)
        except (ConnectionError, RuntimeError) as e:
            st.error(str(e))
            st.stop()
        cancelled = sorted(cancel_seats)
        st.session_state[state_key] = set()
        st.success(f"Cancelled seats: {cancelled}")
        st.rerun()

st.divider()
st.subheader("Change Seat")

reservation_labels = {
    f"Seat {seat}": (res_id, seat)
    for seat, res_id in my_seats.items()
}

with st.form("change_seat"):
    selected_label = st.selectbox("My seat", options=list(reservation_labels.keys()))
    new_seat = st.number_input("New seat number", min_value=1, max_value=capacity, value=1)
    submitted = st.form_submit_button("Update", type="primary")

if submitted:
    res_id, _ = reservation_labels[selected_label]
    try:
        result = api.update_reservation(res_id, int(new_seat))
        if result.get("ok"):
            st.success("Seat updated.")
            st.rerun()
        else:
            st.error("Could not update — seat may already be taken.")
    except (ConnectionError, RuntimeError) as e:
        st.error(str(e))
