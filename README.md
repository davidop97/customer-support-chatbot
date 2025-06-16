# customer-support-chatbot

Chatbot diseñado para la automatización y mejora del servicio de atención al cliente en diversos canales. Facilita la resolución de consultas frecuentes y optimiza la interacción con los usuarios mediante un pipeline RAG (Retrieval-Augmented Generation), una base de datos para gestionar clientes, y una interfaz conversacional basada en Streamlit.

## Descripción General

Este proyecto implementa un asistente virtual para un supermercado que:
- Saluda a los clientes y determina si son nuevos o frecuentes.
- Registra clientes nuevos con validaciones específicas (identificación, nombre, teléfono, correo).
- Valida clientes frecuentes mediante una base de datos SQLite.
- Responde preguntas frecuentes utilizando un pipeline RAG basado en documentos procesados (Horarios.xlsx, Suma_Gana.pdf, Preguntas_Frecuentes.docx).

## Estructura del Proyecto

```
customer-support-chatbot/
├── .venv/                  # Entorno virtual (ignorar)
├── app.py                  # Aplicación Streamlit
├── calculate_effectiveness.py  # Script para calcular efectividad del RAG
├── data/                   # Datos procesados
│   ├── processed/          # Contiene vectordb, chunks.jsonl, y resultados
│   │   ├── vectordb/
│   │   ├── chunks.jsonl
│   │   ├── cleaned_horarios.json
│   │   ├── preguntas_frecuentes.json
│   │   ├── suma_gana.json
│   │   └── rag_eval_results_similarity.csv
│   └── raw/                # Archivos originales
│       ├── Horarios.xlsx
│       ├── Preguntas_Frecuentes.docx
│       └── Suma_Gana.pdf
├── mlruns/                 # Datos de experimentos MLflow
├── src/                    # Código fuente
│   ├── __pycache__/        # Archivos generados (ignorar)
│   ├── chat/               # Módulo para el pipeline RAG
│   │   └── rag_pipeline.py
│   ├── database/           # Módulo para la base de datos
│   │   └── database.py
│   ├── embeddings/         # Módulo para chunking y embeddings
│   │   ├── chunk.py
│   │   └── embed_and_index.py
│   ├── eval/               # Módulo para evaluación
│   │   └── rag_evaluate.py
│   ├── extraction/         # Módulo para extracción de datos
│   │   ├── extract_faqs.py
│   │   ├── extract_schedules.py
│   │   └── extract_pdf.py
│   ├── preprocessing/      # Módulo para preprocesamiento (placeholder)
│   ├── prompts/            # Plantillas de prompts
│   │   ├── v1_asistente_retail.txt
│   │   └── v2_preguntas_faq.txt
│   ├── utils/              # Utilidades
│   ├── __init__.py         # Inicializa el paquete src
│   └── run_pipeline.py     # Orquestador del pipeline RAG
├── test.db                 # Base de datos SQLite
├── .env                    # Variables de entorno
├── .gitignore              # Archivos a ignorar en Git
├── LICENSE.md              # Licencia
├── README.md               # Este archivo
└── requirements.txt        # Dependencias
```

## Requisitos Previos

- Python 3.8+
- Una clave API de OpenAI (almacenada en `.env` como `OPENAI_API_KEY`).
- Dependencias instaladas (ver `requirements.txt`).

### Instalación de Dependencias

1. Clona el repositorio:
   ```bash
   git clone https://github.com/davidop97/customer-support-chatbot.git
   cd customer-support-chatbot
   ```

2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   .venv\Scripts\activate     # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno en `.env`:
   ```env
   OPENAI_API_KEY=tu_clave_de_api_aqui
   VECTORSTORE_PATH=data/processed/vectordb
   PROMPT_DIR=src/prompts
   PROMPT_VERSION=v2_preguntas_faq
   OPENAI_MODEL=gpt-4o
   OPENAI_TEMPERATURE=0
   DATABASE_URL=sqlite:///./test.db
   ```

## Pasos para Configurar y Ejecutar el Proyecto

### Paso 1: Procesamiento de Datos (Extracción y Pipeline RAG)

Los datos se extraen de tres archivos (Horarios.xlsx, Suma_Gana.pdf, Preguntas_Frecuentes.docx) y se procesan para crear chunks y embeddings que alimentan el pipeline RAG.

1. **Extracción de Datos**:
   - Los scripts en `src/extraction/` (extract_schedules.py, extract_pdf.py, extract_faqs.py) extraen el contenido de `Horarios.xlsx`, `Suma_Gana.pdf`, y `Preguntas_Frecuentes.docx` respectivamente.
   - Estos scripts guardan los datos procesados en formato JSON (e.g., `cleaned_horarios.json`, `suma_gana.json`, `preguntas_frecuentes.json`) en `data/processed/`.
   - **Ejecutar manualmente (si es necesario)**:
     - Navega a `src/extraction/` y ejecuta cada script:
       ```bash
       python extract_schedules.py
       python extract_pdf.py
       python extract_faqs.py
       ```
     - Asegúrate de que los archivos originales estén en `data/raw/`.

2. **Ejecutar el Pipeline RAG**:
   - El script `src/run_pipeline.py` orquesta el chunking y la generación de embeddings/indexación.
   - **Cómo correrlo**:
     - Asegúrate de que la clave API de OpenAI esté configurada en `.env` o pásala como argumento.
     - Ejecuta desde la raíz del proyecto:
       ```bash
       python -m src.run_pipeline.py --api_key tu_clave_de_api_aqui --log INFO
       ```
     - O si usas `.env`:
       ```bash
       python -m src.run_pipeline.py --log INFO
       ```
     - **Detalles**:
       - **`run_chunking()`**: Divide los documentos extraídos en chunks y los guarda en `data/processed/chunks.jsonl`.
       - **`run_embed_and_index()`**: Genera embeddings con OpenAI y crea un vectorstore en `data/processed/vectordb`.
       - El script usa logging para informar el progreso y manejará errores (e.g., si no encuentra los chunks).

   - **Verificación**:
     - Confirma que `data/processed/chunks.jsonl` y `data/processed/vectordb` se crearon correctamente.

### Paso 2: Configurar la Base de Datos

La base de datos SQLite (`test.db`) gestiona los registros de clientes.

1. **Inicializar la Base de Datos**:
   - El módulo `src/db/database.py` define la tabla `clientes` y crea la base de datos.
   - Ejecuta desde la raíz:
     ```bash
     python -m src.db.database
     ```
   - Esto creará `test.db` con la tabla `clientes` (id, identificacion, nombre, telefono, email, fecha_registro).

2. **Verificación**:
   - Confirma que `test.db` existe en la raíz del proyecto.

### Paso 3: Ejecutar la Aplicación

La interfaz del chatbot se ejecuta con Streamlit usando `app.py`.

1. **Lanzar la Aplicación**:
   - Asegúrate de que el pipeline RAG y la base de datos estén configurados.
   - Ejecuta desde la raíz:
     ```bash
     streamlit run app.py
     ```
   - Abre el navegador en la URL proporcionada (e.g., `http://localhost:8501`).

2. **Interacción**:
   - El bot saludará y pedirá que indiques si eres "nuevo" o "frecuente".
   - Sigue las instrucciones para registrar datos (si nuevo) o validar tu identificación (si frecuente).
   - Haz preguntas frecuentes (e.g., "¿Cuáles son los horarios?") para probar el pipeline RAG.

### Paso 4: Evaluar el Rendimiento del RAG

Para verificar la efectividad del pipeline RAG (requiere ≥70%):

1. **Ejecutar la Evaluación**:
   - Usa el script `src/eval/rag_evaluate.py`:
     ```bash
     python -m src.eval.rag_evaluate
     ```
   - Esto generará `data/processed/rag_eval_results_similarity.csv`.

2. **Calcular Efectividad**:
   - Ejecuta `calculate_effectiveness.py`:
     ```bash
     python calculate_effectiveness.py
     ```
   - Revisa la salida para ver si superas el 70%.

3. **Visualizar en MLflow**:
   - Inicia el servidor MLflow:
     ```bash
     mlflow ui
     ```
   - Abre `http://localhost:5000` y explora el experimento `rag_evaluation_similarity`.

## Contribuciones

- Reporta issues o sugiere mejoras en el repositorio.
- Envía pull requests con tus cambios.

## Licencia

[MIT License](LICENSE.md)
```

---

### Notas sobre los Cambios

1. **Base de Datos**:
   - Cambié `src/db/models.py` a `src/database/database.py` en las instrucciones.

2. **Archivos de Extracción**:
   - Actualicé los nombres a `extract_schedules.py`, `extract_pdf.py`, y `extract_faqs.py` según la imagen.

3. **Preprocesamiento**:
   - Dejé `src/preprocessing/` como placeholder, ya que la imagen no muestra archivos específicos. Si hay scripts (e.g., `clean_data.py`), añádelos manualmente.

4. **Docker**:
   - Lo dejaremos para después, como acordaste. Podemos retomarlo cuando tengas más tiempo.

---

### Siguientes Pasos

1. **Copia y Pega**:
   - Reemplaza el contenido de `README.md` con el texto anterior.

2. **Verifica**:
   - Asegúrate de que los comandos funcionen (e.g., `python -m src.database.database`).
   - Prueba el flujo completo si tienes tiempo.

3. **Docker**:
   - Cuando estés listo, podemos crear el `Dockerfile` y `.dockerignore`.
