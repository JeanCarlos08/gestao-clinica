# Base leve
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Sistema: dependências básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia deps e instala
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Pasta de uploads persistente
RUN mkdir -p /app/uploads

# Expor porta padrão do Streamlit (alinhado ao config)
EXPOSE 8501

# Comando de inicialização
CMD ["python", "-m", "streamlit", "run", "app.py"]
