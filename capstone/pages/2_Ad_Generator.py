"""
pages/2_Ad_Generator.py — USE CASE 1: Craft a job ad from scratch.

Flow (documented on the Methodology page):
  1. Employer fills in generic, non-PII job details (role, industry,
     seniority, employment type, key skills, optional salary).
  2. A salary benchmark is computed from the consolidated advertised-salaries
     dataset (data/singapore-advertised-salaries-csv.csv).
  3. helper_functions/llm.get_completion() drafts a TAFEP-aligned,
     structured job advertisement from those inputs.
  4. The draft is passed through the SAME compliance engine as Use Case 2
     (logics/check_compliance.check_compliance) as a self-check pass, so
     the generator and the checker close the loop.
"""
import re
from pathlib import Path

import streamlit as st
import pandas as pd

# Same import pattern as capstone_main.py: make sure the capstone folder
# (this page's grandparent) is on the module search path.
import sys, os
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

from utility import check_password
from helper_functions.llm import get_completion
from logics.check_compliance import check_compliance

# Defence in depth: the router already gates every page, but keep the
# check here too in case this page is ever opened standalone.
if not check_password():
    st.stop()

st.title("✍️ Ad Generator")
st.caption(
    "Describe the role and Ad Generator drafts a clear, inclusive, "
    "TAFEP-aligned job advertisement for you."
)

# ----------------------------------------------------------------- data paths
CAPSTONE_DIR = Path(__file__).resolve().parent.parent   # .../capstone
SALARY_CSV = CAPSTONE_DIR / "data" / "singapore-advertised-salaries-csv.csv"

# Fallback industry list mirrors the MOM MRSD (Sep 2025) industry groupings,
# used when the MRSD CSV is not present in capstone/data/.
FALLBACK_INDUSTRIES = [
    "Manufacturing", "Construction", "Wholesale & Retail Trade",
    "Transportation & Storage", "Accommodation & Food Services",
    "Information & Communications", "Financial & Insurance Services",
    "Real Estate Services", "Professional Services",
    "Administrative & Support Services", "Public Administration & Education",
    "Health & Social Services", "Arts, Entertainment & Recreation",
    "Other Community, Social & Personal Services",
]

# Words too generic to be useful when matching a job title in the
# salaries dataset (matching on these would match half the file).
STOP_WORDS = {
    "the", "and", "for", "with", "senior", "junior", "staff", "full",
    "time", "part", "new", "job", "role", "position", "hiring", "wanted",
}


@st.cache_data
@st.cache_data
def load_industries():
    """Industry list from the MRSD by-industry CSV.

    Column layout (verified against the real file): col 0 = SSIC 2020 code,
    col 1 = industry name (merged cells in the source report, so the name
    only appears on the first row of each group -> forward-fill).
    Row 5 of the file is the header row ('Industry'), and the file ends
    with footnote rows — both are filtered out.
    Falls back to a hardcoded list if the file is missing."""
    try:
        ind_csv = CAPSTONE_DIR / "data" / "mrsd_2025_jv_by_ssoc_ind_csv.csv"
        df = pd.read_csv(ind_csv, skiprows=4, header=None,
                         usecols=[0, 1], engine="python")
        df.columns = ["code", "industry"]
        df["industry"] = df["industry"].ffill()
        industries = (
            df["industry"].dropna().astype(str).str.strip().unique().tolist()
        )
        # Drop the header row, footnote rows, and anything that looks like
        # an SSIC code section (e.g. 'S,T,U' or 'C10-32')
        industries = [
            i for i in industries
            if i and i != "nan"
            and i != "Industry"
            and not re.match(r"^\d", i)      # footnotes: '1) Data pertain…'
            and not re.match(r"^[A-Z]\d", i) # SSIC codes: 'C10-32', 'S,T,U'
        ]
        return industries or FALLBACK_INDUSTRIES
    except Exception:
        return FALLBACK_INDUSTRIES


@st.cache_data
def load_salary_data():
    """Load the advertised-salaries dataset (1,000 postings)."""
    df = pd.read_csv(SALARY_CSV)
    df.columns = [c.strip() for c in df.columns]
    df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2
    return df


def salary_benchmark(job_title: str):
    """Match the entered job title against the salaries dataset.

    Returns (n_matches, median_min, median_max) or None when there is not
    enough data to quote a sensible range (fewer than 3 matches)."""
    if not SALARY_CSV.exists():
        return None
    df = load_salary_data()

    words = [w for w in re.findall(r"[a-z]+", job_title.lower())
             if len(w) > 2 and w not in STOP_WORDS]
    if not words:
        return None

    titles = df["Job title"].str.lower()
    mask = pd.Series(False, index=df.index)
    for w in words:
        mask |= titles.str.contains(w, na=False, regex=False)
    matches = df[mask & (df["salary_type"].str.lower() == "monthly")]

    if len(matches) < 3:
        return None
    return (
        len(matches),
        int(matches["salary_min"].median()),
        int(matches["salary_max"].median()),
    )


# ----------------------------------------------------------------- the form
with st.form("ad_details"):
    st.subheader("1. Describe the role")
    job_title = st.text_input("Job title *", placeholder="e.g. Pharmacy Assistant")
    industry = st.selectbox("Industry", load_industries())
    col1, col2 = st.columns(2)
    with col1:
        seniority = st.selectbox(
            "Seniority",
            ("Entry level (no experience required)", "Junior",
             "Mid-level", "Senior", "Managerial"),
        )
    with col2:
        employment_type = st.selectbox(
            "Employment type",
            ("Full-time", "Part-time", "Contract", "Temporary", "Internship"),
        )
    key_skills = st.text_area(
        "Key responsibilities / skills *",
        height=120,
        placeholder="e.g. Pick and pack orders, label products accurately, "
        "simple data entry, comfortable with shift work",
    )
    salary_input = st.text_input(
        "Salary range (optional)",
        placeholder="e.g. $2,800 – $3,400 monthly",
    )
    submitted = st.form_submit_button("Draft my advertisement", use_container_width=True)

# ----------------------------------------------------------------- generation
if submitted:
    if not job_title.strip() or not key_skills.strip():
        st.error("Please fill in at least the job title and key responsibilities.")
        st.stop()

    with st.spinner("Benchmarking salary and drafting your advertisement..."):
        benchmark = salary_benchmark(job_title)
        bench_text = (
            f"- Typical advertised monthly salary for similar roles in the "
            f"consolidated dataset ({benchmark[0]} comparable postings): "
            f"S${benchmark[1]:,} – S${benchmark[2]:,}."
            if benchmark else
            "- No reliable salary benchmark was found for this role in the "
            "consolidated dataset; omit a specific figure or mark it as negotiable."
        )

        prompt = f"""You are FairHire, an assistant that drafts job advertisements for
Singapore employers that comply with the TAFEP guidance and the Tripartite
Guidelines on Fair Employment Practices (TGFEP).

RULES (apply strictly):
- Recruit on merit: focus only on qualifications, skills, knowledge and
  experience relevant to the job.
- Do NOT mention or hint at age, gender, race, religion, marital status,
  family responsibilities, or disability anywhere in the advertisement.
- Do not use age-coded language (e.g. "young", "energetic", "youthful").
- Do not state an age range or a maximum age.
- If the role is physically demanding, describe the physical requirement
  (e.g. "able to lift 10kg") instead of any age or gender criterion.
- Only require a language if the draft role clearly needs it for the stated
  responsibilities, and state the job-related reason next to it.
- Keep every requirement relevant to the job. Do not invent requirements,
  benefits or duties that were not provided.

DRAFT THIS ADVERTISEMENT:
- Job title: {job_title}
- Industry: {industry}
- Seniority: {seniority}
- Employment type: {employment_type}
- Key responsibilities / skills: {key_skills}
- Salary: {salary_input if salary_input.strip() else "(not provided)"}

Salary benchmark from our consolidated dataset (use it to suggest a
reasonable range if the employer did not provide one):
{bench_text}

OUTPUT FORMAT (plain text, no commentary before or after):
Job Title:
Salary: (the provided range, the suggested benchmark range, or "Negotiable")
Working Hours: (typical for the employment type, keep generic)
Job Responsibilities: (bullet list from the provided responsibilities)
Job Requirements: (bullet list; minimum relevant experience/skills only;
  no experience requirement at all if seniority is entry level)
How to Apply: (one short line)"""

        draft = get_completion(prompt, temperature=0)

    st.session_state["generated_draft"] = draft
    st.session_state["draft_inputs"] = job_title

# ------------------------------------------------------------- draft + checks
draft = st.session_state.get("generated_draft")

if draft:
    st.subheader("2. Your draft advertisement")
    if "draft_inputs" in st.session_state:
        b = salary_benchmark(st.session_state["draft_inputs"])
        if b:
            c1, c2, c3 = st.columns(3)
            c1.metric("Comparable postings", f"{b[0]}")
            c2.metric("Typical salary (lower)", f"S${b[1]:,}")
            c3.metric("Typical salary (upper)", f"S${b[2]:,}")
            st.caption(
                "Benchmark from the consolidated advertised-salaries dataset "
                "(median across comparable monthly-salary postings)."
            )

    edited_draft = st.text_area(
        "Review and edit the draft before running the self-check",
        value=draft,
        height=320,
    )

    if st.button("Run self-check against TAFEP guidelines", use_container_width=True):
        with st.spinner("Checking the draft against the official guidelines..."):
            result = check_compliance(
                "Assess this draft job advertisement:\n\n" + edited_draft,
                [],
            )
        st.session_state["draft_assessment"] = result

    assessment = st.session_state.get("draft_assessment")
    if assessment:
        st.subheader("3. Self-check result")
        ans = assessment["answer"]
        m = re.search(r"VERDICT[^A-Za-z\n]*(PASS|MINOR ISSUES|MAJOR ISSUES)",
                      ans, re.IGNORECASE)
        if m:
            v = m.group(1).upper()
            body = re.sub(r"^.*VERDICT.*$", "", ans, count=1,
                          flags=re.IGNORECASE | re.MULTILINE).lstrip()
            if v == "PASS":
                st.success(f"VERDICT: {v} — the draft complies with fair employment guidelines", icon="✅")
            elif v == "MINOR ISSUES":
                st.warning(f"VERDICT: {v} — small improvements recommended", icon="⚠️")
            else:
                st.error(f"VERDICT: {v} — the draft needs changes before publishing", icon="❌")
            st.markdown(body)
        else:
            st.markdown(ans)
        if assessment["sources"]:
            st.caption("Grounded in: " + " · ".join(assessment["sources"]))
        st.info(
            "If the self-check found issues, edit the draft above and run the "
            "self-check again. You can also copy the draft into the FairHire "
            "Checker page for a full interactive review."
        )
