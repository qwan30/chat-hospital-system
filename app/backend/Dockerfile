FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

RUN pip install --no-cache-dir ".[postgres]"

EXPOSE 8000

CMD ["uvicorn", "hospital_ai.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
