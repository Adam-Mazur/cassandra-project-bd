import streamlit as st
import api

st.set_page_config(page_title="My Reservations", page_icon="🎟️", layout="wide")
st.title("My Reservations")

if not st.session_state.get("user"):
    st.warning("Please log in first via the Account page.")
    st.stop()

user = st.session_state["user"]

try:
    all_reservations = api.get_reservations()
    movies = {str(m["movie_id"]): m["title"] for m in api.get_movies()}
    cinemas = {str(c["cinema_id"]): c for c in api.get_cinemas()}
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.stop()

reservations = [
    r for r in all_reservations if str(r["user_id"]) == str(user["user_id"])
]

if not reservations:
    st.info("You have no reservations. Head to Make Reservation to book one.")
    st.stop()

display = [
    {
        "reservation_id": str(r["reservation_id"]),
        "movie": movies.get(str(r["movie_id"]), "Unknown"),
        "cinema": cinemas.get(str(r["cinema_id"]), {}).get("name", "Unknown"),
        "seat": r["seat_number"],
    }
    for r in reservations
]

st.dataframe(display, use_container_width=True)
st.divider()

reservation_labels = {
    f"{d['movie']} @ {d['cinema']} — seat {d['seat']}": d["reservation_id"]
    for d in display
}

col1, col2 = st.columns(2)

with col1:
    st.subheader("Change Seat")
    with st.form("edit_reservation"):
        selected = st.selectbox("Reservation", options=list(reservation_labels.keys()), key="edit_sel")
        cinema_id = next(
            str(r["cinema_id"]) for r in reservations
            if str(r["reservation_id"]) == reservation_labels[selected]
        )
        capacity = cinemas.get(cinema_id, {}).get("capacity", 9999)
        new_seat = st.number_input("New Seat Number", min_value=1, max_value=capacity, value=1)
        submitted = st.form_submit_button("Update", type="primary")
    if submitted:
        try:
            result = api.update_reservation(reservation_labels[selected], int(new_seat))
            if result.get("ok"):
                st.success("Seat updated.")
                st.rerun()
            else:
                st.error("Could not update — seat may already be taken.")
        except (ConnectionError, RuntimeError) as e:
            st.error(str(e))

with col2:
    st.subheader("Cancel Reservation")
    with st.form("cancel_reservation"):
        selected = st.selectbox("Reservation", options=list(reservation_labels.keys()), key="cancel_sel")
        submitted = st.form_submit_button("Cancel", type="primary")
    if submitted:
        try:
            result = api.cancel_reservation(reservation_labels[selected])
            if result.get("ok"):
                st.success("Reservation cancelled.")
                st.rerun()
            else:
                st.error("Could not cancel reservation.")
        except (ConnectionError, RuntimeError) as e:
            st.error(str(e))
