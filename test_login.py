import streamlit as st
from ingest.team_setup import render_team_setup

st.title("Login Page")

if not st.user.is_logged_in:
    st.write("You are not logged in.")
    if st.button("Log in with Google"):
        st.login()
else:
    st.write(f"Logged in as: {st.user.email}")
    render_team_setup()
    if st.button("Log out"):
        st.logout()