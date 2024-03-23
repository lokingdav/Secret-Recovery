#!/bin/bash

# Build the enclave image from docker image
docker build -t sk-enclave -f Dockerfile.enclave .
nitro-cli build-enclave --docker-uri sk-enclave --output-file sk_enclave.eif > nitro-cli-build.log
cat nitro-cli-build.log

# Assign 2 vCPUs and 4096 MiB memory
nitro-cli-config -t 2 -m 4096
nitro-cli run-enclave --eif-path sk_enclave.eif --cpu-count 2 --memory 4096 --enclave-cid 16 --debug-mode