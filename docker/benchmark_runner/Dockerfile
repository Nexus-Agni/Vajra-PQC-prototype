FROM python:3.10-slim

RUN apt-get update && apt-get install -y docker.io curl docker-compose-plugin

WORKDIR /app
COPY docker/benchmark_runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["tail", "-f", "/dev/null"]
