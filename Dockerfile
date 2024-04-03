FROM python:3.12.2-alpine

WORKDIR /app
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY src ./src
EXPOSE 8000
CMD uvicorn src.translation_service_challenge:app --host 0.0.0.0
