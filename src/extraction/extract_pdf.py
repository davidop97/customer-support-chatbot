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

# Patrón para detectar ítems con viñeta o numerados
BULLET_PATTERN = re.compile(r"^•\s+(.*)")
NUMBER_PATTERN = re.compile(r"^(\d+)\.\s+(.*)")

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

    # 2) Separar descripción (antes del primer título)
    description_lines: List[str] = []
    idx = 0
    while idx < len(raw_lines) and raw_lines[idx] not in SECTION_TITLES:
        description_lines.append(raw_lines[idx])
        idx += 1
    descripcion = " ".join(description_lines).strip()

    # 3) Agrupar líneas por sección
    sections_data: Dict[str, List[str]] = {}
    current_title: str = ""
    for ln in raw_lines[idx:]:
        if ln in SECTION_TITLES:
            current_title = ln
            sections_data[current_title] = []
        elif current_title:
            sections_data[current_title].append(ln)

    # 4) Parsear cada sección
    secciones: List[Dict[str, Any]] = []
    for title in SECTION_TITLES:
        lines = sections_data.get(title, [])
        if not lines:
            continue

        # buscar índice del primer ítem
        first_item_idx = None
        for i, line in enumerate(lines):
            if BULLET_PATTERN.match(line) or NUMBER_PATTERN.match(line):
                first_item_idx = i
                break

        # párrafos
        if first_item_idx is None:
            parrafos = [" ".join(lines).strip()]
            items: List[str] = []
            notas: List[str] = []
        else:
            parrafos = [" ".join(lines[:first_item_idx]).strip()] if first_item_idx > 0 else []
            items = []
            # procesar desde el primer ítem
            for line in lines[first_item_idx:]:
                m_b = BULLET_PATTERN.match(line)
                m_n = NUMBER_PATTERN.match(line)
                if m_b:
                    items.append(m_b.group(1).strip())
                elif m_n:
                    items.append(m_n.group(2).strip())
                else:
                    notas.append(line.strip())

        secciones.append({
            "titulo": title,
            **({"parrafos": parrafos} if parrafos else {}),
            **({"items": items}     if items     else {}),
            **({"notas": notas}     if notas     else {}),
        })

    return {
        "programa": pdf_path.stem,
        "descripcion": descripcion,
        "secciones": secciones
    }

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
