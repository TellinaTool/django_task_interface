#!/usr/bin/env bash

until `sudo docker run --rm -p 10412:10412 proxy > proxy.log 2>&1`; do
    echo "Proxy server crashed with exit code $?.  Respawning.." >&2
    sleep 1
done