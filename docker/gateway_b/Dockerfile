FROM phase0-pqc-feasibility-phase0

WORKDIR /app

# Copy packages
COPY packages/qstie-common packages/qstie-common
COPY packages/qstie-trust packages/qstie-trust

# Install dependencies and local packages
RUN pip install --no-cache-dir pytest pytest-asyncio requests pycti ./packages/qstie-common ./packages/qstie-trust

# Copy Gateway B source
COPY gateway_b /app/gateway_b
COPY tests/phase3 /app/tests/phase3

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "-m", "gateway_b.main"]
