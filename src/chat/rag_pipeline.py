import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import logging

from pydantic import SecretStr

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1) Carga .env
load_dotenv()

# 2) Parámetros de entorno
VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", "data/processed/vectordb")
PROMPT_DIR = Path(os.getenv("PROMPT_DIR", "src/prompts"))
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v2_preguntas_faq")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

def load_vectorstore() -> FAISS:
    """Carga el FAISS vectorstore desde disco."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está definida en .env")
        embeddings = OpenAIEmbeddings(api_key=SecretStr(api_key))
        vectorstore = FAISS.load_local(
            folder_path=VECTORSTORE_PATH,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info(f"Vectorstore cargado desde {VECTORSTORE_PATH}")
        return vectorstore
    except Exception as e:
        logger.error(f"Error al cargar vectorstore: {e}")
        raise

def load_prompt() -> PromptTemplate:
    """Carga el template de prompt según la versión seleccionada."""
    prompt_file = PROMPT_DIR / f"{PROMPT_VERSION}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {prompt_file}")
    template = prompt_file.read_text(encoding="utf-8")
    return PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template=template
    )

def build_rag_chain():
    """Construye el chain de RAG listo para usarse."""
    try:
        # a) Vectorstore
        vectordb = load_vectorstore()
        retriever = vectordb.as_retriever(search_kwargs={"k": 5})

        # b) Prompt
        prompt = load_prompt()

        # c) LLM
        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE
        )

        # d) Formatear contexto desde documentos recuperados
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # e) Pipeline RAG
        rag_chain = RunnableSequence(
            {
                "question": RunnablePassthrough() | (lambda x: x["question"]),
                "context": (lambda x: x["question"]) | retriever | format_docs,
                "chat_history": lambda x: x.get("chat_history", [])
            },
            prompt,
            llm,
            lambda x: {"answer": x.content}  # Envolver la salida en un diccionario con clave 'answer'
        )

        # f) Memoria conversacional
        def get_session_history(session_id: str) -> ChatMessageHistory:
            return ChatMessageHistory()

        # g) Chain con historial
        chain = RunnableWithMessageHistory(
            runnable=rag_chain,
            get_session_history=get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

        logger.info("RAG chain construido correctamente")
        return chain

    except Exception as e:
        logger.error(f"Error al construir RAG chain: {e}")
        raise