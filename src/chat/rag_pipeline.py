# src/chat/rag_pipeline.py

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from pydantic import SecretStr

# 1) Carga .env
load_dotenv()

# 2) Parámetros por entorno
VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "data/processed/vectordb")
PROMPT_DIR      = Path(os.getenv("PROMPT_DIR", "src/chat/prompts"))
PROMPT_VERSION  = os.getenv("PROMPT_VERSION", "v1_asistente_retail")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

def load_vectorstore() -> FAISS:
    """Carga el FAISS vectorstore desde disco."""
    api_key = os.environ["OPENAI_API_KEY"]
    embeddings = OpenAIEmbeddings(api_key=SecretStr(api_key))
    return FAISS.load_local(
        folder_path=VECTORSTORE_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )

def load_prompt() -> PromptTemplate:
    """Carga el template de prompt según la versión seleccionada."""
    prompt_file = PROMPT_DIR / f"{PROMPT_VERSION}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {prompt_file}")
    template = prompt_file.read_text(encoding="utf-8")
    return PromptTemplate(
        input_variables=["context", "question", "history"],
        template=template
    )

def build_rag_chain() -> ConversationalRetrievalChain:
    """Construye el chain de RAG listo para usarse."""
    # a) vectorstore
    vectordb = load_vectorstore()
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    # b) prompt
    prompt = load_prompt()

    # c) LLM
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE
    )

    # d) ConversationalRetrievalChain
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True
    )
