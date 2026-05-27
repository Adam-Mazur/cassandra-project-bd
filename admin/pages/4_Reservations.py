import streamlit as st
import api

st.set_page_config(page_title="Reservations", page_icon="🎟️", layout="wide")
st.title("Reservations")

try:
    reservations = api.get_reservations()
    if reservations:
        st.dataframe(reservations, use_container_width=True)
    else:
        st.info("No reservations yet.")
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
