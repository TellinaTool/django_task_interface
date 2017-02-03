#!/usr/bin/env bash

RUN_PROXY=$1

until ${RUN_PROXY}; do
    echo "Proxy server crashed with exit code $?.  Respawning.." >&2
    sleep 1
done