FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Prefer slim Docker deps (see requirements.docker.txt). Full ML stack: requirements.txt
COPY requirements.docker.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.docker.txt

COPY . .

RUN mkdir -p /app/data/uploads /app/data/feedback /app/data/pseudo_labels /app/logs /app/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
