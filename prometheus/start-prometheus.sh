#!/bin/bash

NAME=prometheus-dpfc
PROMETHEUS_BASE="/data/prometheus"
IMAGE="docker.io/prom/prometheus:v2.53.1"
COMMAND='["/bin/prometheus","--config.file=/etc/prometheus/prometheus.yml","--storage.tsdb.path=/prometheus","--web.console.libraries=/usr/share/prometheus/console_libraries","--web.console.templates=/usr/share/prometheus/consoles","--storage.tsdb.retention.time=2y","--storage.tsdb.retention.size=100GB"]'

[[ -d "$PROMETHEUS_BASE" ]] || mkdir -p "$PROMETHEUS_BASE" || { echo "Couldn't create storage directory: $PROMETHEUS_BASE"; exit 1; }


podman rm -f ${NAME}

podman run -d \
    --name ${NAME} \
    --user 0:0 \
    -p 8080:9090 \
    -v "${PROMETHEUS_BASE}/etc:/etc/prometheus" \
    -v "${PROMETHEUS_BASE}/data:/prometheus:rw" \
    --restart=always \
    --entrypoint="${COMMAND}" \
    ${IMAGE}

