from typing import Annotated
import json
from pathlib import Path

from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnableLambda
from langchain_openai import OpenAIEmbeddings
from datetime import datetime

MANUALS_DIR = Path("data/manuals")
TICKETS_PATH = Path("data/tickets.json")

# Run once during start of conversation so we dont have to build the vector store every tool call
def _build_vector_store() -> Chroma:
    # Document Loading
    loader = DirectoryLoader(MANUALS_DIR, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()

    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=120, separators=['\n\n', '\n', '.', ' '])
    chunks = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

    # Build Vector store: Using chromadb for the demo
    vector_store = Chroma.from_documents(documents=chunks, embedding=embeddings)

    return vector_store
    

_vector_store = _build_vector_store()  # built once on import

# Helper function to append retrieved chunks
def format_docs(chunks):
    chunk_texts = [chunk.page_content for chunk in chunks]
    context = '\n\n'.join(chunk_texts)
    return context

@tool
def retrieve_manual_context(query: str) -> str:
    """Retrieves relevant sections from machine manuals based on the query. 
    Use this when the operator asks about machine operation, troubleshooting steps, 
    or needs documentation for a specific machine or process."""
    
    # RAG chain to retrieve relevant machine documentation
    retriever = _vector_store.as_retriever(
        search_kwargs={"k": 3}
    )
    chain = retriever | RunnableLambda(format_docs) 
    relevant_docs = chain.invoke(query)

    return relevant_docs

@tool
def create_escalation_ticket(
    operator_id: Annotated[str, "The operator's ID. Use the operator ID mentioned in the system prompt."],
    issue: Annotated[str, "A clear description of the issue that needs escalation."]
) -> str:
    """Creates an escalation ticket for an operator issue that requires supervisor or engineer attention.
    Use this when the operator explicitly requests escalation or when the issue is beyond their ability to resolve independently."""
    
    ticket = {
        "operator_id": operator_id,
        "issue": issue,
        "timestamp": datetime.now().isoformat()
    }

    tickets = []
    if TICKETS_PATH.exists():
        with open(TICKETS_PATH, "r") as f:
            tickets = json.load(f)

    tickets.append(ticket)

    with open(TICKETS_PATH, "w") as f:
        json.dump(tickets, f, indent=2)

    return f"Ticket raised successfully. Issue logged: {issue}"


@tool
def log_profile_correction(dimension: str, correction: str) -> str:
    """Use this when the operator explicitly corrects an assumption about their preferences or behavior.
    For example: 'I actually prefer visual instructions' or 'I don't escalate quickly, I try to fix things first'."""
    return f"[EXPLICIT PROFILE CORRECTION] Operator has directly stated a preference correction — dimension: {dimension}, correction: {correction}. This signal carries higher weight than inferred behavioral signals."