FROM python:2-slim

MAINTAINER nicolas@movio.co

WORKDIR /usr/src/app

COPY rocksdb_prometheus_exporter/*.py /usr/src/app/rocksdb_prometheus_exporter/
COPY setup.py /usr/src/app/
COPY LICENSE /usr/src/app/

RUN pip install -e .

ENV PORT=8080
ENV INTERVAL=15
ENV TTL=60
ENV PATHS=

CMD python -u /usr/local/bin/rocksdb-prometheus-exporter \
    --port $PORT \
    --interval $INTERVAL \
    --ttl $TTL \
    $PATHS
