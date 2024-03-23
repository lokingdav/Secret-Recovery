#!/bin/bash

# Build the enclave image from docker image
docker build -t sk-enclave -f Dockerfile.enclave .
nitro-cli build-enclave --docker-uri sk-enclave --output-file sk_enclave.eif > nitro-cli-build.log
cat nitro-cli-build.log

# Assign 2 vCPUs and 4096 MiB memory to the enclave
nitro-cli run-enclave --config enclave-config.json
