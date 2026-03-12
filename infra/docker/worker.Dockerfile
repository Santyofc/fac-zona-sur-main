FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ libxmlsec1-dev libxml2-dev libxslt1-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info", "--concurrency=2"]
