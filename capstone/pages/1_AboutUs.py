"""
pages/1_AboutUs.py
About Us page for the FairHire capstone project.
Covers the assignment's "About Us" deliverable: project scope, objectives,
and features. Detailed data sources and data flows live on the
Methodology page (pages/3_Methodology.py) — no duplication here.
"""
import streamlit as st

# Password gate: Streamlit pages run as separate scripts, so every page
# must check the password itself or users could bypass the login by
# navigating directly to this page.
from utility import check_password

if not check_password():
    st.stop()

# ------------------------------------------------------------------ Hero
st.title("ℹ️ About FairHire")
st.subheader("Making recruitment fairer, one job advertisement at a time")

st.write(
    """
    **FairHire** is a capstone project that helps employers in Singapore craft
    clear, inclusive and TAFEP-aligned job advertisements quickly, and to
    transform existing job requirements into a structured job advertisement
    while encouraging fair and inclusive hiring practices.
    """
)

# ------------------------------------------------------- Scope & objectives
st.header("🎯 Project Scope & Objectives")

st.write(
    """
    Employers may unintentionally include wording in job advertisements that
    conflicts with Singapore's fair employment guidelines — for example,
    age preferences, gendered language, or requirements that are not relevant
    to the job. FairHire is a chat-based assistant that reviews job
    advertisements against official guidelines and explains how to improve them.
    """
)

st.markdown(
    """
    | Objective | How FairHire meets it |
    |---|---|
    | **Consolidate information** from multiple official sources | Fair hiring guidelines (TAFEP, MOM) are retrieved live from our knowledge base, and official labour-market statistics (MOM MRSD) provide benchmarks |
    | **Personalise the experience** with generic, non-identifiable inputs | Employers provide only job-related information (role text, pasted ads, uploaded documents, form fields) — no personal data is collected |
    | **Enhance understanding** through interactivity | The assistant explains *why* each flagged phrase is problematic, cites the relevant guideline, and answers follow-up questions in chat |
    | **Present information effectively** | Extracted text is shown in an editable box, assessments appear in a chat interface with a colour-coded verdict, and suggestions distinguish original wording from recommended rewrites |
    """
)

# --------------------------------------------------------------- Data sources
st.header("📚 Data Sources")

st.write(
    """
    FairHire consolidates information from **official and trustworthy,
    publicly accessible sources**: fair-hiring guidance from **TAFEP** and
    **MOM**, official **MOM job-vacancy statistics (MRSD, Sep 2025)**, and a
    consolidated dataset of **advertised salaries**.

    The full list of sources — what each one provides, how it is loaded into
    the knowledge base, and how the data flows through the app — is
    documented on the **🛠️ Methodology page**.
    """
)

# -------------------------------------------------------------------- Features
st.header("✨ Features")

st.subheader("🔍 Use Case 1 — FairHire Checker: assess an existing advertisement")

st.markdown(
    """
    **1. 📝 Flexible input — type, paste, or upload**
    Enter your job advertisement as free text, or upload a PDF or Word
    (.docx) document. Additional instructions typed alongside an upload
    are combined with the document contents.

    **2. ✏️ Review and edit before submitting**
    When a document is uploaded, its text is extracted and displayed
    immediately in an editable box, so you can correct extraction errors
    or trim content before the assessment.

    **3. 🔍 Guideline-based assessment**
    FairHire checks your advertisement against TAFEP and MOM fair-hiring
    guidance and highlights phrases that may not align with fair
    recruitment practices, with explanations grounded in the guidelines.

    **4. 💬 Follow-up questions in chat**
    Ask follow-up questions about the assessment, such as whether a
    specific requirement is acceptable, and get answers based on the
    consolidated guidance.

    **5. 🔁 Edit and resubmit**
    Improve your advertisement directly and resubmit it for a fresh
    assessment — FairHire remembers the conversation, so feedback builds
    on previous rounds.
    """
)

st.subheader("✍️ Use Case 2 — Ad Generator: draft a new advertisement")

st.markdown(
    """
    **1. 📋 Describe the role in a form**
    Fill in generic, non-identifiable details: job title, industry,
    seniority, employment type, and key responsibilities or skills.

    **2. 💰 Built-in salary advisory**
    If you enter a salary range, it is used in the draft as provided.
    If you leave it out, FairHire advises one: the role is matched
    against a consolidated dataset of 1,000 advertised Singapore
    salaries, and the **median advertised range across comparable
    roles** is suggested in the draft — shown to you first as metric
    tiles (comparable postings found, typical lower and upper salary).
    If fewer than 3 comparable postings exist, no figure is invented:
    the draft marks the salary as negotiable instead.

    **3. 🤖 AI-drafted, TAFEP-aligned advertisement**
    The AI drafts a structured advertisement (job title, salary, working
    hours, responsibilities, requirements, how to apply) under strict
    fair-hiring rules: merit-based criteria only, no age-coded or gendered
    language, no invented requirements or benefits.

    **4. ✅ Built-in self-check**
    The draft is then checked by the *same* compliance engine as the
    FairHire Checker. If issues are found, edit the draft and re-run the
    self-check until it passes — generator and checker close the loop.
    """
)

# ------------------------------------------------------------------ Disclaimer
st.info(
    """
    💡 **Our purpose:** help employers spend less time writing job
    advertisements and more time finding the right person for the job —
    while keeping hiring fair, inclusive and focused on what matters:
    skills, qualifications and experience.
    """
)

st.caption(
    "Note: FairHire provides AI-assisted guidance based on publicly available "
    "guidelines and does not constitute legal advice or guarantee compliance "
    "with TAFEP requirements. Employers should review the final advertisement "
    "before publication."
)
