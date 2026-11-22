"""
pages/login.py — Login page shown before the user authenticates.

The router (fairhire_app.py) sends users here while they are not logged
in. It simply renders the password form from utility.check_password();
once the password is accepted, st.rerun() (fired inside check_password)
restarts the router, which then shows the real app navigation.
"""
import streamlit as st
from utility import check_password

# Renders the login form (and sets st.session_state["password_correct"]
# when the right password is submitted).
check_password()
