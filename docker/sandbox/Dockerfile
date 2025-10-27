FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libopenblas-dev \
        liblapack-dev \
        gfortran \
        libffi-dev \
        libssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash sandbox
WORKDIR /home/sandbox

COPY requirements.base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY runner.py /opt/sandbox/runner.py

RUN chown -R sandbox:sandbox /opt/sandbox /home/sandbox
USER sandbox

ENTRYPOINT ["python", "/opt/sandbox/runner.py"]
