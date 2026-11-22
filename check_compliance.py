import streamlit as st
import sys, os, json
import logging # Set logging for the queries

from dotenv import load_dotenv

# Import libraries for web scraping
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import tiktoken

# import llm.py 
#from helper_functions import llm # <--- This is the helper function that we have created

# Setting up credentials for LangChain components
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader # Load text files in a document object
from langchain_core.documents import Document # wrap web scrap contents in a Document object, just like TextLoader does
from langchain_community.document_loaders import PyPDFLoader # Loads PDF in a document object

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from langchain_classic.retrievers.multi_query import MultiQueryRetriever

# Create the compplete Q&A Chain (Pipeline)
from langchain_classic.chains import (
    create_retrieval_chain,
    create_history_aware_retriever
)
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import (
    ChatPromptTemplate, # convert text prompt into LangChain's prompt format
    MessagesPlaceholder,
    # >>> ADD HERE (Change 1 of 6): import PromptTemplate so each chunk passed to the
    # LLM can be prefixed with its document title. Without this import the later
    # document_prompt= line will crash with NameError.
    PromptTemplate
    # <<< END
)

load_dotenv('.env')

# Pass API to LangChain       # Get API from .env file
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')


# embedding model that we will use for the session
embeddings_model = OpenAIEmbeddings(model='text-embedding-3-small')

# llm to be used in RAG pipeplines in this notebook
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0, seed=42)


# go up a dir above where this py file is located to find helper functions
sys.path.append( #Add this folder to the list of places where Python looks for modules when I use import
    os.path.abspath( # give fill absolute path
        os.path.join( #folder1\folder2\.. means go up one level to folder1
            os.path.dirname(__file__), '..'))) # gets folder containing current py file



########### HELPER FUNCTIONS ##########
def count_tokens(text):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    return len(encoding.encode(text))


@st.cache_resource # ADDED new
def create_rag_chain():

    ##### DOC LOADING
    # Placeholder for documents loaded
    list_of_documents_loaded = []


    # >>> ADD HERE (Change 2 of 6): URL -> human-readable title map.
    # The system prompt tells the LLM to cite "exact document titles from metadata",
    # so every document (web page AND PDF) must carry a "title" key.
    DOC_TITLES = {
        "https://www.tal.sg/tafep/employment-practices/recruitment/writing-job-advertisements":
            "TAFEP — Writing Job Advertisements",
        "https://www.straitstimes.com/singapore/jobs/how-tafep-dealt-with-unfair-job-practices":
            "Straits Times — How TAFEP dealt with unfair job practices",
        "https://www.tal.sg/tafep/resources/articles/2020/how-to-avoid-being-discriminatory-in-online-job-ads#":
            "TAFEP — Avoiding discriminatory online job ads",
        "https://www.mom.gov.sg/passes-and-permits/employment-pass/consider-all-candidates-fairly":
            "MOM — Consider all candidates fairly",
        "https://www.tal.sg/tafep/-/media/tal/tafep/resources/tools-and-templates/files/2026/fair-recruitment--selection-publication-nov-2025.pdf":
            "TAFEP — Fair Recruitment & Selection Publication (Nov 2025)",
    }
    # <<< END


    # list of urls to scrape
    url_list = [
        "https://www.tal.sg/tafep/employment-practices/recruitment/writing-job-advertisements",
        "https://www.straitstimes.com/singapore/jobs/how-tafep-dealt-with-unfair-job-practices",
        "https://www.tal.sg/tafep/resources/articles/2020/how-to-avoid-being-discriminatory-in-online-job-ads#",
        "https://www.mom.gov.sg/passes-and-permits/employment-pass/consider-all-candidates-fairly"]


    # Load website contents
    for url in url_list:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find("main")
            markdown_content = md(str(content))

            # wrap in a Document object, just like TextLoader does
            doc = Document(
                page_content=markdown_content,
                # >>> ADD HERE (Change 3 of 6): add the human-readable "title" key
                # alongside the existing "source" URL.
                metadata={"source": url, "title": DOC_TITLES.get(url, url)}
                # <<< END
            )
            list_of_documents_loaded.append(doc)
            print(f"Loaded {url}")

        except Exception as e:
            print(f"Error loading {url}: {e}")
            continue


    # List of PDFs to load as doc
    pdf_urls = [
        "https://www.tal.sg/tafep/-/media/tal/tafep/resources/tools-and-templates/files/2026/fair-recruitment--selection-publication-nov-2025.pdf"
    ] 


    # Load PDFs 
    for pdf_url in pdf_urls: 
        try: 
            loader = PyPDFLoader(pdf_url) 
            pages = loader.load() 

            # >>> ADD HERE (Change 4 of 6): stamp every PDF page with the document
            # title BEFORE extending the list. Every page must get the "title" key,
            # because the document_prompt below references {title} for every chunk —
            # a single page without it raises a missing-variable error at runtime.
            # (PyPDFLoader already stores the page number in each page's metadata,
            # so it is kept automatically.)
            for page in pages:
                page.metadata["title"] = DOC_TITLES.get(pdf_url, pdf_url)
            # <<< END

            list_of_documents_loaded.extend(pages) 

            print(f"Loaded PDF: {pdf_url}") 
            print(f"Pages loaded: {len(pages)}") 

        except Exception as e: 
            print(f"Error loading PDF: {pdf_url}") 
            print(f"Error: {e}") 


    #print("Total documents loaded:", len(list_of_documents_loaded)) 


    ####### SPLITTING and CHUNKING 
    # In this case, we intentionally set the chunk_size to 1100 tokens, to have the smallest document (document 2) intact 
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, 
        chunk_overlap=10,
        length_function=count_tokens
    ) 

    # Split the documents into smaller chunks 
    splitted_documents = text_splitter.split_documents(list_of_documents_loaded) 

    # Print the number of documents after splitting 
    #print(f"Number of documents after splitting: {len(splitted_documents)}") 


    ########### EMBEDDING AND STORING IN VECTORDB 
    # Embed each chunk and load it into the vector store. 
    
    # Reset any existing collection first
    Chroma(
        collection_name='embedding_semantic',
        persist_directory='./vector_db'
    ).reset_collection()

    # Then rebuild the collection with the latest documents
    vectordb = Chroma.from_documents(
        splitted_documents, 
        embeddings_model, 
        collection_name='embedding_semantic', 
        persist_directory='./vector_db'
    ) 


    ######### REFINEMENT PRE_RETRIEVAL STAGE 
    retriever_multiquery = MultiQueryRetriever.from_llm( 
        retriever=vectordb.as_retriever(), 
        llm=llm, 
    ) 


    ######## INVOKING 
    #question = "Create a job advertisement template" 
    # unique_docs = retriever_multiquery.invoke(question) 
    # len(unique_docs) 


    ######## CHAINING TOGETHER 

    # NEW: Prompt to rewrite follow-up questions using the previous conversation
    contextualize_q_system_prompt = """
    Given the chat history and the latest user question,
    rewrite the latest question so that it can be understood
    independently without needing the chat history.

    Do not answer the question.
    Only rewrite it if necessary.
    If it is already clear, return it as it is.
    """

    # NEW: This prompt receives the previous chat messages and the latest question
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    # NEW: Make the retriever aware of the chat history
    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever_multiquery,
        contextualize_q_prompt
    )


    # Note that the `retriever_multiquery` is used as the retriever 
    # rather than the `vectordb` and its as_retriever() method that we used in the previous examples 
    system_prompt = """You are FairHire, a compliance assessment assistant for Singapore
fair employment practices. You assess job advertisements against the TAFEP guidance
and the Tripartite Guidelines on Fair Employment Practices (TGFEP) found in the
retrieved context below.

GROUNDING RULES (apply strictly):
- Base every finding ONLY on the retrieved context. Do not rely on your own knowledge
  of Singapore employment rules.
- When citing a rule, name the source it came from (e.g. "TAFEP — Writing Job
  Advertisements"). If the context does not clearly support a finding, say
  "not covered by the retrieved guidelines" instead of guessing.
- Do not thank the user, do not make small talk, and do not role-play a chatbot.
  You are producing a compliance assessment.

  REWRITE RULES (apply strictly):
- At the end of ISSUES FOUND, always output a final section:
  FULL REWRITE: <a complete, corrected job advertisement that resolves ALL issues
  found above simultaneously>
- Each individual "Suggested rewrite" must not reintroduce any wording flagged in
  any other issue (e.g. no rewrite may contain "male", "young", or an age range).
- Never invent justifications the employer did not provide. If a requirement (such
  as a language) needs a job-related reason, use the placeholder
  "[state the job-related reason]" instead of making one up.
- Never add new requirements, benefits, or duties that were not in the original
  advertisement.
- Assess EVERY sentence of the advertisement. If a clause is acceptable, it may be
  omitted from ISSUES FOUND, but do not silently drop between-run findings without
  reason.
- Cite sources only by their exact document titles from the retrieved context
  metadata. Never invent a source name.

OUTPUT FORMAT — follow exactly:

VERDICT: PASS | MINOR ISSUES | MAJOR ISSUES

ISSUES FOUND:
For each issue (most severe first), output:
  - Criterion at risk: (e.g. age / gender / race / religion / marital status /
    nationality / language / disability / irrelevant requirement)
  - Severity: High / Medium / Low
  - Quoted from the advertisement: "<exact words from the user's ad — the quote
    MUST contain the specific violating phrase itself; e.g. for an age issue,
    the actual age range like 'Age 25–35' must appear in the quote>"
  - Why it is a problem: <one sentence, grounded in the cited guideline>
  - Source: <which retrieved guideline document this comes from>
  - Suggested rewrite: "<the exact replacement wording, ready to paste>"

CRITERIA MET:
List the fair-employment criteria the advertisement already satisfies, if any.

NOTES:
Anything the retrieved guidelines do not clearly cover.

If the input is a follow-up question rather than an advertisement, answer it using
the retrieved context only, and keep the same factual, cited style.

Retrieved context:
{context}"""


    # NEW: Add MessagesPlaceholder so the LLM can see previous conversation messages
    qa_prompt = ChatPromptTemplate.from_messages([ 
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("user", "Question: {input}")
    ]) 

    # >>> ADD HERE (Change 5 of 6): document_prompt controls how EACH retrieved chunk
    # is rendered before being stuffed into {context}. This is the line that makes
    # the titles actually VISIBLE to the LLM — metadata alone is not sent to the
    # model, only the rendered text is. Requires the PromptTemplate import from
    # Change 1, and the "title" key on every document from Changes 3 and 4.
    document_prompt = PromptTemplate.from_template(
        "Source: {title}\n{page_content}"
    )
    # <<< END

    # This creates a chain that takes the retrieved documents, combines their text into the {context} placeholder, and sends the prompt to your LLM.
    #The word stuff refers to putting the retrieved document contents together into the prompt.
    combine_docs_chain = create_stuff_documents_chain(llm, qa_prompt, document_prompt=document_prompt) 

    # NEW: Use history_aware_retriever instead of retriever_multiquery
    qa_chain_multiquery = create_retrieval_chain( 
        history_aware_retriever,
        combine_docs_chain, 
    ) 

    return qa_chain_multiquery




def check_compliance(user_prompt, chat_history=None):

    # Create the RAG chain
    qa_chain_multiquery = create_rag_chain()

    # Send user's job advertisement and previous conversation to the RAG chain
    result = qa_chain_multiquery.invoke({
        'input': user_prompt,
        'chat_history': chat_history or []
    })

    # Collect the unique source documents that were actually retrieved,
    # so the UI can show which guidelines the assessment is grounded in.
    # >>> ADD HERE (Change 6 of 6): collect the human-readable "title"
    # (fall back to the URL if a title is ever missing).
    sources = []
    for doc in result.get("context", []):
        src = doc.metadata.get("title") or doc.metadata.get("source", "")
        if src and src not in sources:
            sources.append(src)
    # <<< END

    return {"answer": result["answer"], "sources": sources}

######################## HELPER FUNCTIONS ##########################
