import streamlit as st
import api

st.set_page_config(page_title="Reservations", page_icon="🎟️", layout="wide")
st.title("Reservations")

try:
    reservations = api.get_reservations()
    movies = {str(m["movie_id"]): m["title"] for m in api.get_movies()}
    cinemas = {str(c["cinema_id"]): c["name"] for c in api.get_cinemas()}
    users = {str(u["user_id"]): u["name"] for u in api.get_users()}
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
    st.stop()

if not reservations:
    st.info("No reservations yet.")
    st.stop()

display = [
    {
        "user": users.get(str(r["user_id"]), str(r["user_id"])),
        "movie": movies.get(str(r["movie_id"]), str(r["movie_id"])),
        "cinema": cinemas.get(str(r["cinema_id"]), str(r["cinema_id"])),
        "seat": r["seat_number"],
        "reservation_id": str(r["reservation_id"]),
    }
    for r in reservations
]

st.dataframe(display, use_container_width=True)
