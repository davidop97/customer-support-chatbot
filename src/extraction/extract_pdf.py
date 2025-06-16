from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import re
import json

# Títulos exactos que marcan el inicio de cada sección
SECTION_TITLES = [
    "Acumulación de puntos",
    "Inscríbete a Suma y Gana",
    "Consulta de puntos",
    "Redención de puntos",
    "Vigencia de los puntos",
    "Beneficios adicionales",
]

# Patrones para detectar ítems con viñeta o numerados
BULLET_PATTERN = re.compile(r'^\u2022\s+(.+)$')
NUMBER_PATTERN = re.compile(r'^(\d+)\.\s+(.+)$')

def clean_line(line: str) -> str:
    """Limpia la línea eliminando emoticones y caracteres no estándar, preservando viñetas durante procesamiento."""
    line = re.sub(r'[^\w\s.,:;?!¿¡áéíóúÁÉÍÓÚñÑ$\u2022]', '', line)
    line = re.sub(r'\s+', ' ', line.strip())
    return line

def debug_char(line: str):
    """Muestra el primer carácter y su código Unicode para depuración."""
    if line:
        char = line[0]
        return f"Char: {char!r}, Unicode: U+{ord(char):04X}"
    return "Empty line"

def extract_sections_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """
    Extrae del PDF un JSON con esta estructura:
    {
      "programa": "...",
      "descripcion": "...",
      "secciones": [
         {
           "titulo": "...",
           "parrafos": ["..."],       # texto antes de los ítems
           "items": ["...", "..."],   # líneas con • o 1., 2., 3.
           "notas": ["...", "..."]    # texto posterior a los ítems
         },
         ...
      ]
    }
    """
    # 1) Leer todas las líneas del PDF
    raw_lines: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for ln in text.splitlines():
                if ln.strip():
                    raw_lines.append(ln.strip())
                    print(f"DEBUG: Línea cruda: {ln.strip()} [{debug_char(ln)}]")

    # 2) Separar descripción (antes del primer título)
    description_lines: List[str] = []
    idx = 0
    while idx < len(raw_lines) and clean_line(raw_lines[idx]) not in SECTION_TITLES:
        description_lines.append(clean_line(raw_lines[idx]))
        idx += 1
    descripcion = " ".join(description_lines).strip()
    print(f"DEBUG: Descripción: {descripcion}")

    # 3) Agrupar líneas por sección
    sections_data: Dict[str, List[str]] = {title: [] for title in SECTION_TITLES}
    current_title: str = ""
    for ln in raw_lines[idx:]:
        cleaned = clean_line(ln)
        if cleaned in SECTION_TITLES:
            current_title = cleaned
            print(f"DEBUG: Nueva sección: {current_title}")
        elif current_title:
            sections_data[current_title].append(ln)

    # 4) Parsear cada sección
    secciones: List[Dict[str, Any]] = []
    for title in SECTION_TITLES:
        lines = sections_data.get(title, [])
        if not lines:
            print(f"DEBUG: Sección vacía: {title}")
            continue

        parrafos = []
        items = []
        notas = []
        in_list = False
        current_item = None
        item_count = 0

        print(f"DEBUG: Procesando sección: {title}")
        for i, line in enumerate(lines):
            cleaned = clean_line(line)
            print(f"DEBUG: Línea {i+1}: {line} [Cleaned: {cleaned}] [{debug_char(line)}]")
            m_b = BULLET_PATTERN.match(line)
            m_n = NUMBER_PATTERN.match(line)

            # Detectar inicio de lista por ":" en la línea anterior
            if i > 0 and clean_line(lines[i-1]).endswith(':'):
                in_list = True
                print("DEBUG: Inicio de lista detectado por ':' en línea anterior")

            if m_b is not None:
                in_list = True
                item_text = m_b.group(1).strip()
                items.append(clean_line(item_text))
                current_item = clean_line(item_text)
                item_count += 1
                print(f"DEBUG: Ítem detectado ({item_count}): {item_text}")
            elif m_n is not None:
                in_list = True
                item_text = m_n.group(2).strip()
                items.append(clean_line(item_text))
                current_item = clean_line(item_text)
                item_count += 1
                print(f"DEBUG: Ítem detectado ({item_count}): {item_text}")
            elif in_list and current_item and (
                len(cleaned.split()) <= 10 or
                (len(cleaned.split()) <= 15 and not cleaned.lower().startswith(('en tienda', 'además', 'al completar', 'podrás', 'unirse al')))
            ):
                # Concatenar como continuación de ítem
                current_item += " " + cleaned.strip()
                items[-1] = current_item
                print(f"DEBUG: Continuación de ítem: {cleaned}")
            elif in_list and len(cleaned.split()) <= 10:
                # Tratar como ítem sin viñeta en lista
                items.append(cleaned)
                current_item = cleaned
                item_count += 1
                print(f"DEBUG: Ítem sin viñeta detectado ({item_count}): {cleaned}")
            else:
                in_list = False
                if not items:
                    parrafos.append(cleaned.strip())
                    print(f"DEBUG: Párrafo: {cleaned}")
                else:
                    notas.append(cleaned.strip())
                    print(f"DEBUG: Nota: {cleaned}")

        # Unir párrafos y notas si hay múltiples líneas
        parrafos_text = [" ".join(parrafos)] if parrafos else []
        notas_text = [" ".join(notas)] if notas else []

        section_data = {
            "titulo": title,
            **({"parrafos": parrafos_text} if parrafos_text else {}),
            **({"items": items} if items else {}),
            **({"notas": notas_text} if notas_text else {}),
        }
        secciones.append(section_data)
        print(f"DEBUG: Sección procesada: {title}, Ítems contados: {item_count}")

    result = {
        "programa": pdf_path.stem,
        "descripcion": descripcion,
        "secciones": secciones
    }
    print(f"DEBUG: Total secciones: {len(secciones)}")
    return result

if __name__ == "__main__":
    import sys
    pdf_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/Suma_Gana.pdf")
    result = extract_sections_from_pdf(pdf_file)
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_file.stem}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON generado en: {out_path}")