FROM python:3.10-slim

RUN apt-get update && apt-get install -y docker.io curl iputils-ping iproute2 \
    && mkdir -p /usr/libexec/docker/cli-plugins/ \
    && curl -SL https://github.com/docker/compose/releases/download/v2.26.1/docker-compose-linux-x86_64 -o /usr/libexec/docker/cli-plugins/docker-compose \
    && chmod +x /usr/libexec/docker/cli-plugins/docker-compose

WORKDIR /app
COPY docker/benchmark_runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["tail", "-f", "/dev/null"]
