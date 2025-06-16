import time
import json
import mlflow
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from src.chat.rag_pipeline import build_rag_chain
from langchain_openai import OpenAIEmbeddings
import numpy as np
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# 1) Carga dataset de prueba
DATASET = Path("data/processed/preguntas_frecuentes.json")
with DATASET.open(encoding="utf-8") as f:
    qa_list = json.load(f)

# 2) Inicializa chain y embeddings
chain = build_rag_chain()
embeddings = OpenAIEmbeddings(api_key=(os.getenv("OPENAI_API_KEY")))

def calculate_cosine_similarity(text1: str, text2: str) -> float:
    """Calcula la similitud coseno entre dos textos."""
    emb1 = embeddings.embed_query(text1)
    emb2 = embeddings.embed_query(text2)
    return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

# 3) Inicia experimento MLflow
mlflow.set_experiment("rag_evaluation_similarity")
with mlflow.start_run(run_name="eval_faq_similarity"):
    mlflow.log_param("n_samples", len(qa_list))
    results = []

    for qa in tqdm(qa_list, desc="Evaluando preguntas"):
        q = qa["pregunta"]
        expected = qa["respuesta"] if isinstance(qa["respuesta"], str) else qa["respuesta"].get("texto", "")
        t0 = time.time()
        out = chain.invoke(
            {"question": q},
            config={"configurable": {"session_id": "eval_session"}}
        )
        latency = time.time() - t0
        answer = out["answer"]  # Usar out["answer"] por la corrección en rag_pipeline.py
        # Evaluación: similitud coseno
        similarity = calculate_cosine_similarity(expected, answer)
        match = int(similarity >= 0.8)  # Umbral de similitud (ajustable)
        results.append({
            "pregunta": q,
            "esperada": expected,
            "obtenida": answer,
            "latency": latency,
            "similarity": similarity,
            "match": match
        })
        # Registra métricas
        mlflow.log_metric("latency_ms", latency * 1000)
        mlflow.log_metric("similarity", similarity)
        mlflow.log_metric("match", match)

    # 4) Guarda resultados a CSV y lo sube como artifact
    df = pd.DataFrame(results)
    csv_path = "data/processed/rag_eval_results_similarity.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    mlflow.log_artifact(csv_path, artifact_path="evaluation")
    print(f"Evaluación guardada en {csv_path}")