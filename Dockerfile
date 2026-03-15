FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --upgrade pip

COPY requirements.txt ./

RUN python -m pip install -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src

CMD ["python", "-m", "streamlit", "run", "src/mindstream/ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
