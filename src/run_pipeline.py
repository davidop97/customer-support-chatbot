import argparse
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from embeddings.chunk import run_chunking
from embeddings.embed_and_index import run_embed_and_index

# Cargar variables de entorno desde .env
load_dotenv()


def setup_logging(level: str):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=getattr(logging, level.upper(), logging.INFO)
    )
    
    # Silenciar los mensajes INFO de faiss
    logging.getLogger("faiss").setLevel(logging.WARNING)


def main(api_key: str):
    logging.info("Iniciando pipeline de RAG")
    try:
        logging.info("1) Chunking de documentos...")
        run_chunking()
    except Exception:
        logging.exception("Error en chunking, abortando pipeline.")
        sys.exit(1)

    chunks_file = Path("data/processed/chunks.jsonl")
    if not chunks_file.exists():
        logging.error(f"No encontré {chunks_file}, asegúrate de que run_chunking() generó los chunks.")
        sys.exit(1)

    try:
        logging.info("2) Generando embeddings e indexando vectorstore...")
        run_embed_and_index(openai_api_key=api_key)
    except Exception:
        logging.exception("Error al generar embeddings o guardar vectorstore.")
        sys.exit(1)

    logging.info("Pipeline completo: chunks & vectorstore listos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador de chunking + embedding")
    parser.add_argument(
        "--api_key", "-k",
        help="OpenAI API key (si no, toma OPENAI_API_KEY del entorno)"
    )
    parser.add_argument(
        "--log", "-l",
        default="INFO",
        help="Nivel de logging (DEBUG, INFO, WARNING, ERROR)"
    )
    args = parser.parse_args()
    setup_logging(args.log)
    key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        logging.error("No se encontró OPENAI_API_KEY. Define la var de entorno o pásala con --api_key.")
        sys.exit(1)

    main(key)
