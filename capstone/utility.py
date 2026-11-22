import streamlit as st

def check_password():
    # If the user has already logged in, let them continue
    # False below means user has not log in before, function returns false and skip the 'return true'
    if st.session_state.get("password_correct", False):
        return True #immediately exits the function

    st.title("FairHire App — Login")

    with st.form("password_form"):
        password = st.text_input("Enter password", type="password") # type pw hides the password as we type
        submitted = st.form_submit_button("Log in")

    if submitted:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True #create session_state dict's key and value , update value to True to indicate user has alr log in for this session
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

    return st.session_state.get("password_correct", False)
