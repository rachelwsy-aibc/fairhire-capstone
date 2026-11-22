"""
pages/1_AboutUs.py
About Us page for the FairHire capstone project.
Covers the assignment's "About Us" deliverable: project scope, objectives,
data sources, and features.
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
    | **Personalise the experience** with generic, non-identifiable inputs | Employers provide only job-related information (role text, pasted ads, uploaded documents) — no personal data is collected |
    | **Enhance understanding** through interactivity | The assistant explains *why* each flagged phrase is problematic, cites the relevant guideline, and answers follow-up questions in chat |
    | **Present information effectively** | Extracted text is shown in an editable box, assessments appear in a chat interface, and suggestions distinguish original wording from recommended rewrites |
    """
)

# --------------------------------------------------------------- Data sources
st.header("📚 Data Sources")

st.write(
    """
    FairHire consolidates information from official and trustworthy,
    publicly accessible sources. Fair-hiring guidance is retrieved at
    runtime from a searchable knowledge base built from the sources below.
    """
)

st.markdown(
    """
    | Source | What it provides | How it is used |
    |---|---|---|
    | [TAFEP — Writing Job Advertisements](https://www.tal.sg/tafep/employment-practices/recruitment/writing-job-advertisements) | Do's and don'ts for fair job advertisements | Compliance review knowledge base |
    | [TAFEP — Tripartite Guidelines on Fair Employment Practices](https://www.tal.sg/tafep/getting-started/fair/tripartite-guidelines) | The five principles of fair employment practices | Grounding for assessment explanations |
    | [TAFEP — Avoiding discriminatory job ads](https://www.tal.sg/tafep/resources/articles/2020/how-to-avoid-being-discriminatory-in-online-job-ads) | Real-life examples of biased vs fair wording | Few-shot guidance for rewrites |
    | [MOM — Consider all candidates fairly](https://www.mom.gov.sg/passes-and-permits/employment-pass/consider-all-candidates-fairly) | Fair consideration requirements for job postings | Compliance review knowledge base |
    | [MOM — Job Vacancies (MRSD), Sep 2025](https://stats.mom.gov.sg/) | Official job vacancy counts by industry, occupational group and minimum qualification (3 CSV files in `data/`) | Labour-market context and benchmarks |
    | Singapore advertised salaries dataset (1,000 postings, in `data/`) | Advertised salary ranges, minimum experience and key skills by role | Salary and requirement benchmarks |
    """
)

# -------------------------------------------------------------------- Features
st.header("✨ Features")

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
