"""
fairhire_app.py — FairHire app entrypoint (router).

Run the app with:
    streamlit run capstone/fairhire_app.py
(launch from the AIBootCamp2026 folder)

IMPORTANT: st.navigation is called on EVERY run — before AND after
login. If the not-logged-in branch stopped the script before
st.navigation ran, Streamlit falls back to automatic page discovery
(entry file first, then pages/ order) — which is why the sidebar
previously showed "fairhire app" above "About Us" pre-login.
"""
import streamlit as st

st.set_page_config(
    layout="centered",
    page_title="FairHire App",
)

# Pages (list order = sidebar order: About Us first, then the checker)
about_page = st.Page("pages/1_AboutUs.py", title="About Us", icon="ℹ️")
main_page = st.Page("capstone_main.py", title="FairHire Checker", icon="🔍")
gen_page = st.Page("pages/2_Ad_Generator.py", title="Ad Generator", icon="✍️")
login_page = st.Page("pages/login.py", title="Login", icon="🔒", default=True)
method_page = st.Page("pages/3_Methodology.py", title="Methodology", icon="🛠️")


if st.session_state.get("password_correct", False):
    # Logged in: real app, correct sidebar order
    pg = st.navigation([about_page, main_page, gen_page, method_page])
    pg.run()
else:
    # Not logged in: only the Login page exists (a single-page
    # navigation hides itself, so the sidebar stays clean)
    st.navigation([login_page]).run()
