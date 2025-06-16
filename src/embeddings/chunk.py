from pathlib import Path
import json
from typing import List, Dict, Any

PROCESSED_DIR = Path("data/processed")
CHUNKS_PATH   = PROCESSED_DIR / "chunks.jsonl"

def load_json_docs() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []

    for file in PROCESSED_DIR.glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        source = file.stem.lower()

        # 1) 'Suma y Gana': descripción general + fragmentos por sección
        if source == "suma_gana" and isinstance(data, dict):
            desc = data.get("descripcion", "").strip()
            if desc:
                docs.append({
                    "id": f"{source}-descripcion",
                    "source": source,
                    "section": "descripcion",
                    "text": desc
                })
            # Inicializar contadores por sección
            section_counters = {
                sec.get("titulo", ""): {"para": 0, "item": 0, "note": 0}
                for sec in data.get("secciones", [])
            }
            for sec in data.get("secciones", []):
                title = sec.get("titulo", "").strip()
                cnt = section_counters[title]
                # Párrafos
                for p in sec.get("parrafos", []):
                    docs.append({
                        "id": f"{source}-{title}-para-{cnt['para']}",
                        "source": source,
                        "section": title,
                        "text": p.strip()
                    })
                    cnt["para"] += 1
                # Ítems
                for it in sec.get("items", []):
                    docs.append({
                        "id": f"{source}-{title}-item-{cnt['item']}",
                        "source": source,
                        "section": title,
                        "text": it.strip()
                    })
                    cnt["item"] += 1
                # Notas
                for n in sec.get("notas", []):
                    docs.append({
                        "id": f"{source}-{title}-note-{cnt['note']}",
                        "source": source,
                        "section": title,
                        "text": n.strip()
                    })
                    cnt["note"] += 1

        # 2) 'Horarios': un fragmento por día
        elif source.startswith("cleaned_horarios") and isinstance(data, list):
            for entry in data:
                suc = entry.get("sucursal", "")
                for dia, h in entry.get("horario", {}).items():
                    if h:
                        docs.append({
                            "id": f"{source}-{suc}-{dia}",
                            "source": source,
                            "section": suc,
                            "text": f"{dia}: {h}"
                        })

        # 3) 'Preguntas frecuentes': un fragmento por pregunta+respuesta
        elif source.startswith("preguntas_frecuentes") and isinstance(data, list):
            for idx, faq in enumerate(data):
                pregunta = faq.get("pregunta", "").strip()
                resp = faq.get("respuesta")
                if isinstance(resp, dict):
                    texto = resp.get("texto", "").strip()
                    items = resp.get("items", [])
                    respuesta = texto + ("\n" + "\n".join(items) if items else "")
                else:
                    respuesta = str(resp).strip()
                docs.append({
                    "id": f"{source}-{idx}",
                    "source": source,
                    "section": faq.get("categoria", ""),
                    "text": f"P: {pregunta}\nR: {respuesta}"
                })

        # 4) Genérico: vuelca cada elemento de la lista o dict
        else:
            if isinstance(data, list):
                for idx, x in enumerate(data):
                    docs.append({
                        "id": f"{source}-{idx}",
                        "source": source,
                        "section": "",
                        "text": json.dumps(x, ensure_ascii=False)
                    })
            else:
                docs.append({
                    "id": source,
                    "source": source,
                    "section": "",
                    "text": json.dumps(data, ensure_ascii=False)
                })

    return docs


def run_chunking():
    docs = load_json_docs()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CHUNKS_PATH.open("w", encoding="utf-8") as fout:
        for doc in docs:
            fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f" Generados {len(docs)} chunks en {CHUNKS_PATH}")


if __name__ == "__main__":
    run_chunking()
