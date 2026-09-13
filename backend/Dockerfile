FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app
RUN pip install --no-cache-dir .
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
RUN mkdir -p /app/data/uploads /app/data/exports
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
