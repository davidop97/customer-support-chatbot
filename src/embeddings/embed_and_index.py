from pathlib import Path
import json
import os
import subprocess

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
# from dotenv import load_dotenv
import mlflow
from langchain.docstore.document import Document
from pydantic import SecretStr

# Cargar variables de entorno desde .env
# load_dotenv()

# Rutas
CHUNKS_PATH = Path("data/processed/chunks.jsonl")
VECTOR_DIR  = Path("data/processed/vectordb")

def load_chunks() -> list[Document]:
    docs: list[Document] = []
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            docs.append(Document(
                page_content=rec["text"],
                metadata={
                    "id": rec["id"],
                    "source": rec["source"],
                    "section": rec["section"]
                }
            ))
    return docs

def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"

def run_embed_and_index(openai_api_key: str | None = None):
    # 1) API Key
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "No se encontró OPENAI_API_KEY. Define la variable de entorno "
            "o pásala como parámetro a run_embed_and_index(openai_api_key=...)."
        )

    # 2) Cargar documentos
    docs = load_chunks()
    print(f" Cargando {len(docs)} documentos para embedding")

    # 3) Instanciar embeddings
    embeddings = OpenAIEmbeddings(api_key=SecretStr(api_key))

    # 4) Construir FAISS
    vectordb = FAISS.from_documents(docs, embeddings)

    # 5) Guardar en disco
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(VECTOR_DIR))
    print(f" Vectorstore guardado en: {VECTOR_DIR}")

    # 6) Tracking en MLflow
    mlflow.set_experiment("vectorstore_build")
    with mlflow.start_run(run_name="build_vectordb"):
        mlflow.log_param("n_docs", len(docs))
        mlflow.log_param("vectordb_path", str(VECTOR_DIR))
        # Taguear commit de Git
        mlflow.set_tag("git_commit", get_git_commit())

if __name__ == "__main__":
    run_embed_and_index()
