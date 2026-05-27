import streamlit as st
import api

st.set_page_config(page_title="Users", page_icon="👤", layout="wide")
st.title("Users")

try:
    users = api.get_users()
    if users:
        st.dataframe(users, use_container_width=True)
    else:
        st.info("No users yet.")
except (ConnectionError, RuntimeError) as e:
    st.error(str(e))
