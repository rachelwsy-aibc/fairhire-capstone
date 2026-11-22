
import streamlit as st
from utility import check_password
# users upload documents
from pypdf import PdfReader
from docx import Document

from logics.check_compliance import check_compliance

# # helper_functions is a folder in same directory, and llm.py is a script within containing helper functions
#from helper_functions import llm  #<< dont need anymore as its called un customer_query_handler


# Check password before showing the app
if not check_password(): # if user has logged in, check_password() is 'True'. not + 'True' returns false + 
    st.stop()


# endregion <--------- Streamlit App Configuration --------->

st.title("Welcome to FairHire")

# STEP 1: Initialise chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

import re

# Verdict banner styling: maps the parsed verdict to a Streamlit banner style
VERDICT_STYLES = {
    "PASS":         "success",  # green box  ✅
    "MINOR ISSUES": "warning",  # amber box  ⚠️
    "MAJOR ISSUES": "error",    # red box    ❌
}

def render_verdict(answer):
    """Detect the VERDICT line in the assessment and render it as a
    colour-coded banner (green tick / amber warning / red cross), then
    show the full report below without the duplicated VERDICT line.

    Falls back to a neutral warning if no verdict can be parsed —
    it never assumes PASS.
    """
    match = re.search(
        r"VERDICT[^A-Za-z\n]*(PASS|MINOR ISSUES|MAJOR ISSUES)",
        answer,
        re.IGNORECASE,
    )

    if match:
        verdict = match.group(1).upper()

        # Remove the original VERDICT line so it isn't shown twice
        body = re.sub(
            r"^.*VERDICT.*$", "", answer, count=1,
            flags=re.IGNORECASE | re.MULTILINE,
        ).lstrip()

        style = VERDICT_STYLES[verdict]
        if style == "success":
            st.success(
                f"VERDICT: {verdict} — this advertisement complies with fair employment guidelines",
                icon="✅",
            )
        elif style == "warning":
            st.warning(
                f"VERDICT: {verdict} — some improvements recommended",
                icon="⚠️",
            )
        else:
            st.error(
                f"VERDICT: {verdict} — this advertisement does not comply with fair employment guidelines",
                icon="❌",
            )

        st.markdown(body)
    else:
        # Missing or unrecognisable verdict: neutral banner, never a false PASS
        st.warning(
            "Could not determine an overall verdict from the assessment below.",
            icon="⚠️",
        )
        st.markdown(answer)

# STEP 1: Allow users to type or upload their job advertisement

st.markdown("""
### Making recruitment fairer, one job advertisement at a time.

FairHire helps employers review their job advertisements
against Singapore's fair recruitment practices and guidelines.

### How does it work?

**Step 1: Prepare your job advertisement**

Have your job advertisement ready in text, PDF or Word format.

**Step 2: Submit your advertisement**

Paste your advertisement into the text box or upload your document.

**Step 3: Review the assessment**

FairHire will assess your advertisement and highlight areas
that may not align with fair recruitment practices.

**Step 4: Improve your advertisement**

Receive explanations and suggestions on how to make your
advertisement more inclusive and fair.

---

### Let's get started!

Submit your job advertisement below to begin your assessment.
""")

# Option 1: Type or paste job advertisement

# Option 1: Type or paste job advertisement
user_text = st.text_area(
    "Type or paste your job advertisement or additional instructions here",
    height=200
)

st.write("OR")

# Option 2: Upload job advertisement
uploaded_file = st.file_uploader(
    "Upload your job advertisement",
    type=["pdf", "docx"]
)

# Initialise extracted_text
extracted_text = ""

# Extract text from uploaded document
if uploaded_file is not None:

    if uploaded_file.name.lower().endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)

        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""

    elif uploaded_file.name.lower().endswith(".docx"):
        document = Document(uploaded_file)

        for paragraph in document.paragraphs:
            extracted_text += paragraph.text + "\n"

    # Display extracted text
    st.subheader("Extracted Job Advertisement")

    extracted_text = st.text_area(
        "Review and edit your job advertisement before submitting",
        value=extracted_text,
        height=250
    )

# STEP 2: Combine typed text and uploaded document text

if uploaded_file is not None:

    user_prompt = f"""
Additional instructions or information from user:
{user_text}

Uploaded job advertisement:
{extracted_text}
"""
else:
    user_prompt = user_text


#if form.form_submit_button("Submit"):
if st.button("Submit"):

    # displays a small temporary notification
    st.toast(f"User Input Submitted - {user_prompt}")

    # NEW: Save the user's prompt to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_prompt
    })

    # NEW: Get previous conversation, excluding the latest user prompt
    previous_chat_history = st.session_state.chat_history[:-1]

    # NEW: Convert Streamlit chat history into LangChain message format
    formatted_chat_history = []

    for message in previous_chat_history:

        if message["role"] == "user":
            formatted_chat_history.append(
                ("human", message["content"])
            )

        elif message["role"] == "assistant":
            formatted_chat_history.append(
                ("ai", message["content"])
            )

    # NEW: Handles errors gracefully
    try:
        # NEW: Pass both the current question and previous conversation to check_compliance()
        result = check_compliance(
            user_prompt,
            formatted_chat_history
        )

        # Saves the result
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"]
        })

                # Colour-coded verdict banner + full report below it
        render_verdict(result["answer"])

        # Show the official sources that were retrieved for this assessment
        if result["sources"]:
            st.caption("Grounded in: " + " · ".join(result["sources"]))

    except Exception as e:
        # NEW: Print the full exception to the terminal for debugging
        print(f"Error in check_compliance: {e}")

        # NEW: Display a friendly error message in the app
        st.error("Sorry, something went wrong while checking your job advertisement. Please try again.")  # NEW

        # Save a fallback message so chat history remains complete, instead of having no response. 
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Sorry, I couldn't check your job advertisement due to an error. Please try again."
        })

# STEP: Display the conversation history
st.subheader("Chat History")

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.write(message["content"])

# STEP : Allow the user to clear the conversation
if st.button("Clear Chat", key="clear_chat"):
    st.session_state.chat_history = []
    st.rerun()
