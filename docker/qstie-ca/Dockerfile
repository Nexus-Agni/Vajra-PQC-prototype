FROM phase0-pqc-feasibility-phase0

WORKDIR /app

# Copy packages
COPY packages/qstie-common packages/qstie-common
COPY packages/qstie-trust packages/qstie-trust

# Install them
RUN pip install pytest ./packages/qstie-common ./packages/qstie-trust

# Script to run the offline CA generation
COPY scripts/bootstrap_pki.py scripts/bootstrap_pki.py

ENTRYPOINT ["python", "scripts/bootstrap_pki.py"]
