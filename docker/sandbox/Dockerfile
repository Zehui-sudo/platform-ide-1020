FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash sandbox
WORKDIR /home/sandbox

COPY runner.py /opt/sandbox/runner.py

RUN chown -R sandbox:sandbox /opt/sandbox /home/sandbox
USER sandbox

ENTRYPOINT ["python", "/opt/sandbox/runner.py"]
