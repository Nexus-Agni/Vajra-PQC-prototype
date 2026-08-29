FROM phase0-pqc-feasibility-phase0

WORKDIR /app

# Copy packages
COPY packages/qstie-common packages/qstie-common
COPY packages/qstie-trust packages/qstie-trust

# Install dependencies and local packages
RUN apt-get update && apt-get install -y iproute2 iputils-ping && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest pytest-asyncio requests zmq misp-stix stix2 liboqs-python cryptography prometheus_client ./packages/qstie-common ./packages/qstie-trust

# Copy Gateway A source
COPY gateway_a /app/gateway_a
COPY tests/phase4 /app/tests/phase4

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "-m", "gateway_a.main"]
