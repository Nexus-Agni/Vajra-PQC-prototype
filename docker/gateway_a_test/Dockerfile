FROM phase0-pqc-feasibility-phase0

WORKDIR /app

# Copy packages
COPY packages/qstie-common packages/qstie-common
COPY packages/qstie-trust packages/qstie-trust

# Install dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio requests pycti zmq misp-stix stix2 liboqs-python cryptography ./packages/qstie-common ./packages/qstie-trust

ENV PYTHONPATH=/app
ENTRYPOINT ["pytest"]
