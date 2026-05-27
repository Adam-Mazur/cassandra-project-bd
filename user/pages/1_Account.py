import streamlit as st
import api

st.set_page_config(page_title="Account", page_icon="👤", layout="wide")
st.title("Account")

if st.session_state.get("user"):
    user = st.session_state["user"]
    st.success(f"Logged in as **{user['name']}** ({user['email']})")
    if st.button("Log out"):
        del st.session_state["user"]
        st.rerun()
    st.stop()

login_tab, register_tab = st.tabs(["Login", "Register"])

with login_tab:
    with st.form("login"):
        email = st.text_input("Email")
        submitted = st.form_submit_button("Login", type="primary")
    if submitted:
        if not email.strip():
            st.error("Email cannot be empty.")
        else:
            try:
                users = api.get_users()
                user = next((u for u in users if u["email"] == email.strip()), None)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Welcome back, {user['name']}!")
                    st.rerun()
                else:
                    st.error("No account found with that email.")
            except (ConnectionError, RuntimeError) as e:
                st.error(str(e))

with register_tab:
    with st.form("register"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Create Account", type="primary")
    if submitted:
        if not name.strip() or not email.strip():
            st.error("Name and email are required.")
        else:
            try:
                api.create_user(name.strip(), email.strip())
                users = api.get_users()
                user = next((u for u in users if u["email"] == email.strip()), None)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Account created! Welcome, {user['name']}!")
                    st.rerun()
            except (ConnectionError, RuntimeError) as e:
                st.error(str(e))
