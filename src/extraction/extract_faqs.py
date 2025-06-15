import os
import json
from typing import List, Dict
from docx import Document
import re

def read_docx_file(file_path: str) -> List[str]:
    """Lee el archivo DOCX y devuelve una lista de líneas de texto."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no existe.")
    
    try:
        doc = Document(file_path)
        lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        print(f"DEBUG: Líneas leídas del DOCX: {len(lines)}")
        return lines
    except Exception as e:
        raise ValueError(f"Error al leer el archivo DOCX: {str(e)}")

def clean_text(text: str) -> str:
    """Limpia el texto eliminando emojis y normalizando espacios."""
    # Elimina emojis (rango Unicode para emojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticonos
        "\U0001F300-\U0001F5FF"  # Símbolos y pictogramas
        "\U0001F680-\U0001F6FF"  # Transporte y símbolos
        "\U0001F1E0-\U0001F1FF"  # Banderas
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(r"", text)
    # Normaliza espacios
    return re.sub(r'\s+', ' ', text.strip())

def parse_faqs(lines: List[str]) -> List[Dict]:
    """Parsea las líneas del documento en una lista de preguntas frecuentes."""
    faqs = []
    current_category = None
    current_question = None
    current_answer: List[str] = []
    
    # Lista de categorías esperadas (sin emojis)
    valid_categories = [
        "Horarios y Atención",
        "Pedidos y Entregas",
        "Pagos y Facturación"
    ]
    
    for i, line in enumerate(lines):
        cleaned_line = clean_text(line)
        if not cleaned_line:
            continue
        
        print(f"DEBUG: Procesando línea {i+1}: {cleaned_line}")
        
        # Ignora el título del documento
        if cleaned_line.startswith("Preguntas Frecuentes"):
            continue
        
        # Detecta categorías
        if cleaned_line in valid_categories:
            if current_question and current_answer:
                faqs.append({
                    "categoria": current_category,
                    "pregunta": current_question,
                    "respuesta": ' '.join(current_answer).strip()
                })
                print(f"DEBUG: FAQ guardada: {current_question} (Categoría: {current_category})")
            current_category = cleaned_line.lower().replace(' ', '-')
            current_question = None
            current_answer = []
            continue
        
        # Detecta preguntas (comienzan con ¿)
        if cleaned_line.startswith('¿'):
            if current_question and current_answer:
                faqs.append({
                    "categoria": current_category,
                    "pregunta": current_question,
                    "respuesta": ' '.join(current_answer).strip()
                })
                print(f"DEBUG: FAQ guardada: {current_question} (Categoría: {current_category})")
            # Extrae solo la pregunta hasta el primer punto o fin de línea
            question_match = re.match(r'^(¿[^?]+\?)', cleaned_line)
            if question_match:
                current_question = question_match.group(1).strip()
                # Si hay texto después de la pregunta, agrégalo como inicio de la respuesta
                remaining_text = cleaned_line[len(current_question):].strip()
                current_answer = [remaining_text] if remaining_text else []
            else:
                current_question = cleaned_line
                current_answer = []
            continue
        
        # Agrega líneas a la respuesta actual (si hay pregunta)
        if current_question:
            current_answer.append(cleaned_line)
    
    # Agrega la última FAQ si existe
    if current_question and current_answer:
        faqs.append({
            "categoria": current_category,
            "pregunta": current_question,
            "respuesta": ' '.join(current_answer).strip()
        })
        print(f"DEBUG: Última FAQ guardada: {current_question} (Categoría: {current_category})")
    
    print(f"DEBUG: Total FAQs extraídas: {len(faqs)}")
    return faqs

def save_to_json(data: List[Dict], output_file: str) -> None:
    """Guarda los datos procesados en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Datos guardados exitosamente en {output_file}")
    except Exception as e:
        raise IOError(f"Error al guardar el archivo JSON: {str(e)}")

if __name__ == "__main__":
    try:
        # Define las rutas de los archivos de entrada y salida
        input_file = "data/raw/Preguntas_Frecuentes.docx"
        output_file = "data/processed/preguntas_frecuentes.json"
        
        # Lee y procesa el documento
        lines = read_docx_file(input_file)
        faqs = parse_faqs(lines)
        
        # Guarda en JSON
        save_to_json(faqs, output_file)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)