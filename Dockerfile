# Usar una imagen base de Python
FROM python:3.13.1-slim

# Actualizar paquetes del sistema para reducir vulnerabilidades
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto para Streamlit
EXPOSE 8501

# Variables de entorno
ENV OPENAI_API_KEY=tu_clave_de_api_aqui
ENV DATABASE_URL=sqlite:///./test.db

# Comando para ejecutar el pipeline y la app
CMD ["sh", "-c", "python -m src.run_pipeline.py --log INFO && streamlit run app.py"]