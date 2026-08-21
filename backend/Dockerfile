FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN grep -v "^xgboost" requirements.txt > requirements_no_xgb.txt && \
    pip install --no-cache-dir --timeout=300 --retries=20 -r requirements_no_xgb.txt && \
    pip install --no-cache-dir --timeout=600 --retries=30 --no-deps xgboost==2.1.1

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
