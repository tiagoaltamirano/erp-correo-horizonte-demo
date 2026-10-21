FROM python:3.12.13-slim
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY src ./src
COPY tools ./tools
COPY tests ./tests
COPY config ./config
COPY compose.yaml ./compose.yaml
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "src.servicio:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
