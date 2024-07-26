#!/bin/bash

NAME=grafana
IMAGE="docker.io/grafana/grafana:10.2.4"
BASE_DIR="/data/grafana"
[[ -d "$BASE_DIR" ]] || mkdir -p "$BASE_DIR" || { echo "Couldn't create storage directory: $BASE_DIR"; exit 1; }

loginctl enable-linger

podman run -d \
    --name ${NAME}\
    -p 3000:3000 \
    --restart=always \
    ${IMAGE}

loginctl disable-linger
