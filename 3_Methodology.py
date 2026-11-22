"""
pages/3_Methodology.py — REQUIRED DELIVERABLE: Methodology page.

Per the assignment brief (Project Type 2 — Capstone Assignment,
Deliverable 2 "Documentation as Pages in the Streamlit Application"):

  "Methodology" Page
  - A comprehensive explanation of the data flows and implementation details.
  - A flowchart illustrating the process flow for each use case in the
    application. Each use case should have its own flowchart.

Both flowcharts are rendered with st.graphviz_chart from DOT strings —
Streamlit renders these client-side (d3-graphviz in the browser), so no
system Graphviz installation is needed.
"""
import streamlit as st

# Same import pattern as the other pages: make sure the capstone folder
# (this page's parent) is on the module search path.
import sys, os
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

from utility import check_password

# Defence in depth: the router (fairhire_app.py) already gates every page,
# but keep the check here too in case this page is opened standalone.
if not check_password():
    st.stop()

st.title("🛠️ Methodology")
st.caption(
    "How FairHire is built: information sources, data flows, and the "
    "process flow for each use case."
)

# ============================================================================
# SECTION 1 — OVERVIEW
# ============================================================================
st.header("1. Overview")

st.markdown(
    """
    **FairHire** is a chat-based assistant that helps Singapore employers
    produce job advertisements aligned with fair employment practices. It
    implements **two use cases**:

    1. **Ad Generator (Use Case 1)** — an employer describes a role in a
       form, and the app drafts a structured, TAFEP-aligned job
       advertisement, then self-checks the draft against the official
       guidelines.
    2. **FairHire Checker (Use Case 2)** — an employer submits an existing
       job advertisement (typed, pasted, PDF or DOCX), and the app assesses
       it against the guidelines, explaining every issue with citations and
       suggested rewrites.

    **Technique stack:** Retrieval-Augmented Generation (RAG) over official
    guideline sources, prompt engineering with strict grounding and
    structured-output rules, and a salary/market benchmark computed from
    consolidated labour-market datasets.

    **Models used** (both via the OpenAI API):
    """
)

st.markdown(
    """
    | Model | Used for | Settings |
    |---|---|---|
    | `gpt-4o-mini` | Compliance assessment (Use Case 2), draft generation (Use Case 1), query contextualisation and multi-query expansion | `temperature=0`, `seed=42` |
    | `text-embedding-3-small` | Embedding guideline chunks for the vector store | default dimensions |
    """
)

# ============================================================================
# SECTION 2 — INFORMATION SOURCES
# ============================================================================
st.header("2. Information Sources & Consolidation")

st.markdown(
    """
    The knowledge base consolidates **five official and trustworthy,
    publicly accessible sources** on fair hiring. All are loaded when the
    RAG chain is first built each session (cached with
    `st.cache_resource`):
    """
)

st.markdown(
    """
    | Source | Type | Role |
    |---|---|---|
    | [TAFEP — Writing Job Advertisements](https://www.tal.sg/tafep/employment-practices/recruitment/writing-job-advertisements) | Web page (scraped) | Compliance rules for age, gender, race, religion, language, nationality in job ads |
    | [Straits Times — How TAFEP dealt with unfair job practices](https://www.straitstimes.com/singapore/jobs/how-tafep-dealt-with-unfair-job-practices) | Web page (scraped) | Real enforcement case studies |
    | [TAFEP — Avoiding discriminatory online job ads](https://www.tal.sg/tafep/resources/articles/2020/how-to-avoid-being-discriminatory-in-online-job-ads#) | Web page (scraped) | Biased vs fair wording examples |
    | [MOM — Consider all candidates fairly](https://www.mom.gov.sg/passes-and-permits/employment-pass/consider-all-candidates-fairly) | Web page (scraped) | Fair-consideration requirements for job postings |
    | [TAFEP — Fair Recruitment & Selection Publication (Nov 2025)](https://www.tal.sg/tafep/-/media/tal/tafep/resources/tools-and-templates/files/2026/fair-recruitment--selection-publication-nov-2025.pdf) | PDF (`PyPDFLoader`) | Detailed fair recruitment and selection guidance |
    """
)

st.markdown(
    """
    Two **structured datasets** (in `capstone/data/`) support Use Case 1:

    - **MOM MRSD Job Vacancies (as at September 2025)** — official vacancy
      counts by industry, occupational group and minimum qualification.
      The by-industry table (`mrsd_2025_jv_by_ssoc_ind_csv.csv`) populates
      the Industry dropdown (vacancy figures are rounded to the nearest
      ten in the source).
    - **Consolidated advertised-salaries dataset** — 1,000 advertised job
      postings with salary range, salary type, minimum experience and key
      skills (`singapore-advertised-salaries-csv.csv`), used for the
      salary benchmark.
    """
)

# ============================================================================
# SECTION 3 — KNOWLEDGE-BASE CONSTRUCTION
# ============================================================================
st.header("3. Knowledge-Base Construction (offline, once per session)")

st.markdown(
    """
    The ingestion pipeline in `logics/check_compliance.py`
    (`create_rag_chain()`, cached with `@st.cache_resource`) runs these
    steps before the first query of a session:

    1. **Scrape** each guideline web page with `requests` +
       `BeautifulSoup`, extracting the `<main>` content and converting it
       to Markdown with `markdownify`.
    2. **Wrap** each page in a LangChain `Document` with metadata
       `{"source": <url>, "title": <human-readable title>}` — titles come
       from a `DOC_TITLES` mapping so citations use real document names.
    3. **Load** the TAFEP PDF with `PyPDFLoader` and stamp every page with
       the same `title` metadata.
    4. **Chunk** all documents with `RecursiveCharacterTextSplitter`
       (`chunk_size=400` tokens, `chunk_overlap=10`, counted with
       `tiktoken`).
    5. **Embed** every chunk with `text-embedding-3-small` and store it in
       a **Chroma** vector database (`collection_name='embedding_semantic'`,
       `persist_directory='./vector_db'`). The collection is reset and
       rebuilt on each fresh process, so the store always reflects the
       current sources.
    """
)

st.markdown(
    """
    Each stored chunk therefore carries its source URL and document title;
    the answer chain renders every retrieved chunk as
    `Source: {title}` (via a `document_prompt`), which is what allows the
    LLM to cite real guideline documents instead of inventing names.
    """
)

# ============================================================================
# FLOWCHART DOT SOURCES
# ============================================================================
FLOWCHART_1_DOT = """
digraph usecase2 {
    rankdir=TB;
    splines=ortho;
    node [fontname="Helvetica", fontsize=10, style=filled, fillcolor="#E8F0FE", color="#4285F4"];
    edge [fontname="Helvetica", fontsize=9, color="#5F6368"];

    start [label="1. User opens\\nFairHire Checker", shape=oval, fillcolor="#D2E3FC"];
    gate [label="2. Password\\ncorrect?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    login [label="2a. Show login form", shape=box, fillcolor="#FCE8E6", color="#EA4335"];
    mode [label="3. Choose input mode", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    paste [label="4a. Type / paste ad\\nin text area", shape=box];
    upload [label="4b. Upload PDF / DOCX\\n(pypdf / python-docx)", shape=box];
    editup [label="4c. Editable review\\nof extracted text", shape=box];
    concat [label="5. Concatenate typed\\ninstructions + document text", shape=box];
    hist [label="6. Format chat history\\nfor LangChain", shape=box];
    ctx [label="7. History-aware retriever:\\ncontextualise query", shape=box];
    multi [label="8. MultiQueryRetriever:\\ngenerate query variants", shape=box];
    chroma [label="9. Chroma vector DB\\nTAFEP + MOM guidelines", shape=cylinder, fillcolor="#FEF7E0", color="#F9AB00"];
    retrieve [label="10. Retrieve top chunks\\n(source + title metadata)", shape=box];
    llm [label="11. Stuff-documents chain:\\nsystem prompt with grounding +\\nrewrite rules, gpt-4o-mini", shape=box, fillcolor="#E6F4EA", color="#34A853"];
    out [label="12. Structured output:\\nVERDICT / ISSUES FOUND /\\nCRITERIA MET / NOTES /\\nFULL REWRITE", shape=box, fillcolor="#E6F4EA", color="#34A853"];
    banner [label="13a. Render verdict banner\\ngreen PASS / amber MINOR / red MAJOR", shape=box];
    sources [label="13b. Render 'Grounded in'\\nsources caption", shape=box];
    follow [label="14. Follow-up question\\nor edited ad?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    endn [label="15. End: user improves\\nad externally", shape=oval, fillcolor="#D2E3FC"];

    start -> gate;
    gate -> login [label=" no"];
    login -> gate [label=" resubmit"];
    gate -> mode [label=" yes"];
    mode -> paste [label=" paste"];
    mode -> upload [label=" upload"];
    upload -> editup -> concat;
    paste -> concat;
    concat -> hist -> ctx -> multi -> chroma;
    chroma -> retrieve -> llm -> out;
    out -> banner;
    out -> sources;
    banner -> follow;
    follow -> hist [label=" yes: next round"];
    follow -> endn [label=" no"];
}
"""

FLOWCHART_2_DOT = """
digraph usecase1 {
    rankdir=TB;
    splines=ortho;
    node [fontname="Helvetica", fontsize=10, style=filled, fillcolor="#E8F0FE", color="#4285F4"];
    edge [fontname="Helvetica", fontsize=9, color="#5F6368"];

    start [label="1. User opens\\nAd Generator", shape=oval, fillcolor="#D2E3FC"];
    gate [label="2. Password\\ncorrect?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    login [label="2a. Show login form", shape=box, fillcolor="#FCE8E6", color="#EA4335"];
    form [label="3. Form: job title, industry\\n(from MRSD CSV), seniority,\\nemployment type, key skills,\\noptional salary", shape=box];
    valid [label="4. Title + key skills\\nfilled in?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    err [label="4a. Show error message", shape=box, fillcolor="#FCE8E6", color="#EA4335"];
    bench [label="5. Salary benchmark: match title\\nwords against advertised-salaries\\nCSV (monthly postings, stop-words\\nfiltered)", shape=box];
    enough [label="6. 3 or more comparable\\npostings?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    tiles [label="6a. Show metric tiles:\\nmedian min-max across matches", shape=box];
    negotiable [label="6b. Benchmark text:\\n'no reliable benchmark;\\nmark negotiable'", shape=box];
    prompt [label="7. Build draft prompt:\\nTAFEP RULES + form inputs\\n+ benchmark", shape=box];
    gen [label="8. LLM call: get_completion\\n(gpt-4o-mini, temperature=0)", shape=box, fillcolor="#E6F4EA", color="#34A853"];
    draft [label="9. Draft advertisement\\n(structured format)", shape=box];
    review [label="10. Editable review box", shape=box];
    selfchk [label="11. Run self-check?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    engine [label="12. check_compliance()\\nsame RAG engine as Use Case 2\\n(see Flowchart 1, steps 7-13)", shape=box, fillcolor="#FEF7E0", color="#F9AB00"];
    verdict [label="13. Verdict?", shape=diamond, fillcolor="#FCE8E6", color="#EA4335"];
    ready [label="14. Draft ready -\\ncopy to job portal", shape=oval, fillcolor="#D2E3FC"];
    back [label="13a. Edit draft per issues found", shape=box];

    start -> gate;
    gate -> login [label=" no"];
    login -> gate [label=" resubmit"];
    gate -> form [label=" yes"];
    form -> valid;
    valid -> err [label=" no"];
    err -> form;
    valid -> bench [label=" yes"];
    bench -> enough;
    enough -> tiles [label=" yes"];
    enough -> negotiable [label=" no"];
    tiles -> prompt;
    negotiable -> prompt;
    prompt -> gen -> draft -> review -> selfchk;
    selfchk -> engine [label=" yes"];
    selfchk -> review [label=" edit first"];
    engine -> verdict;
    verdict -> ready [label=" PASS"];
    verdict -> back [label=" MINOR / MAJOR"];
    back -> review;
}
"""

# ============================================================================
# SECTION 4 — USE CASE 2 + FLOWCHART 1
# ============================================================================
st.header("4. Use Case 2 — FairHire Checker: Assess an Existing Job Ad")

st.markdown(
    """
    **Data flow.** After the password gate, the employer either types or
    pastes the advertisement, or uploads a **PDF / DOCX** — extracted with
    `pypdf` / `python-docx` into an **editable** review box, and any typed
    instructions are **concatenated** with the document text. The combined
    prompt plus the formatted chat history go to `check_compliance()`
    (`logics/check_compliance.py`):

    1. A **history-aware retriever** first contextualises the question
       against the chat history (so follow-ups like *"and what about the
       age requirement?"* retrieve correctly).
    2. A **MultiQueryRetriever** expands it into several search variants
       and retrieves the top chunks from the Chroma vector database.
    3. A **stuff-documents chain** passes the chunks (each rendered with
       its `Source: {title}`) and the ad into `gpt-4o-mini` under the
       system prompt's **grounding rules** (findings only from retrieved
       context; invented justifications replaced by
       `[state the job-related reason]`) and **rewrite rules** (each
       rewrite must resolve every issue simultaneously; every clause
       assessed; citations must use real document titles).
    4. The **structured output** — `VERDICT` / `ISSUES FOUND` /
       `CRITERIA MET` / `NOTES` / `FULL REWRITE` — is rendered as a
       colour-coded verdict banner (green ✅ PASS / amber ⚠️ MINOR /
       red ❌ MAJOR) with a **"Grounded in" caption** listing the retrieved
       sources. Follow-up questions feed back into the same chain via the
       chat history.
    """
)

st.subheader("Flowchart 1 — Process flow for Use Case 2")
st.graphviz_chart(FLOWCHART_1_DOT)
st.caption(
    "Figure 1 — Use Case 2: assessment of an existing job advertisement. "
    "Diamonds are decision points; the cylinder is the vector database; "
    "the loop at step 14 supports follow-up questions and edit-and-resubmit."
)

# ============================================================================
# SECTION 5 — USE CASE 1 + FLOWCHART 2
# ============================================================================
st.header("5. Use Case 1 — Ad Generator: Draft a TAFEP-Aligned Job Ad")

st.markdown(
    """
    **Data flow.** The employer fills a form of **generic, non-identifiable
    inputs** only (job title, industry, seniority, employment type, key
    responsibilities/skills, optional salary). Two data-grounded steps run
    before generation:

    - **Industry list** — parsed from the MOM MRSD by-industry CSV
      (`load_industries()`), with column forward-fill for the source
      report's merged cells and footnote/header filtering.
    - **Salary benchmark** — `salary_benchmark()` matches the job title
      against the advertised-salaries dataset (word match with stop-word
      filtering, monthly postings only); with **3 or more** comparable
      postings it shows median min–max metric tiles, otherwise the prompt
      instructs the model to mark salary negotiable rather than invent a
      figure.

    The draft prompt encodes **TAFEP-aligned rules**: merit-based criteria
    only; no mention or hint of age, gender, race, religion, marital
    status, family responsibilities or disability; no age-coded language
    ("young", "energetic"); physical demands described as requirements
    (e.g. "able to lift 10kg") instead of age/gender criteria; language
    requirements only with a stated job-related reason; no invented
    requirements or benefits. The draft is produced by
    `helper_functions/llm.get_completion()` and shown in an **editable
    review box**.

    **Closing the loop:** the *same* compliance engine as Use Case 2
    (`check_compliance()`) then self-checks the edited draft. If the
    verdict is not PASS, the employer edits and re-checks until the draft
    is ready — the generator and the checker share one grounded engine.
    """
)

st.subheader("Flowchart 2 — Process flow for Use Case 1")
st.graphviz_chart(FLOWCHART_2_DOT)
st.caption(
    "Figure 2 — Use Case 1: generating a fair job advertisement from form "
    "inputs. Step 12 reuses the Use Case 2 compliance engine (Flowchart 1, "
    "steps 7–13) as a self-check subprocess."
)

# ============================================================================
# SECTION 6 — DESIGN DECISIONS & KNOWN LIMITATIONS
# ============================================================================
st.header("6. Design Decisions & Known Limitations")

st.markdown(
    """
    **Design decisions** (each adopted after systematic testing):

    | Decision | Motivation |
    |---|---|
    | Grounding rules: findings only from retrieved context | Early testing showed the model producing correct-sounding findings from its own knowledge rather than the guidelines |
    | Invented justifications replaced by `[state the job-related reason]` | The model once "justified" an unexplained Mandarin requirement with a fabricated client-facing reason — the placeholder asks the employer for the real one |
    | Document titles in chunk metadata + `document_prompt` | Without visible titles the model cited invented source names; now every citation maps to a real loaded document |
    | Structured output format (VERDICT / ISSUES / …) | Enables the colour-coded verdict banner and makes assessments comparable across runs |
    | Lazy imports of the LLM/RAG stack inside button handlers | Keeps page navigation fast; heavy modules load only when a spinner is already showing |
    | `temperature=0`, `seed=42` | Reduces run-to-run variation in assessments |

    **Known limitations:**

    - Retrieval sometimes cites a single document even when several are
      retrieved (observed on the clean-ad test); retrieval quality varies
      with query phrasing.
    - Clauses not covered by the retrieved guidelines (e.g. overtime
      requirements) are routed to NOTES rather than ISSUES FOUND; the
      taxonomy rule reduces but cannot eliminate mis-categorisation.
    - Assessments are AI-assisted guidance, not legal advice (see the
      disclaimer on the About Us page).
    """
)

st.markdown(
    """
    **Test evidence** (same-session runs on the deployed prompt):

    | Test input | Expected | Observed |
    |---|---|---|
    | Unfair ad (age range, "male", "Mandarin speakers only", daily overtime) | MAJOR ISSUES with per-issue citations | ✅ 4 findings, real document titles, verbatim quotes, placeholder for the missing language justification, clean FULL REWRITE |
    | Clean ad (experience, duties, justified Mandarin requirement, salary) | PASS, no over-flagging | ✅ PASS; the justified Mandarin requirement was listed under CRITERIA MET |
    | Realistic full ad (shifts, hourly rates, experience-welcome wording) | PASS, no false positives | ✅ PASS; "experience will be an advantage" correctly not treated as a protected-characteristic preference |
    """
)
