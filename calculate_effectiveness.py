import pandas as pd

# Cargar resultados
results = pd.read_csv("data/processed/rag_eval_results_similarity.csv")

# Calcular efectividad
total = len(results)
successes = results["match"].sum()
effectiveness = (successes / total) * 100

print(f"Efectividad del RAG: {effectiveness:.2f}%")
print(f"Total preguntas: {total}")
print(f"Aciertos: {successes}")
if effectiveness >= 70:
    print("¡Felicidades! Superaste el 70% requerido.")
else:
    print("No alcanzaste el 70%. Considera mejorar el vectorstore o el prompt.")