docker rm -f skrecovery

docker build -t skrecovery -f Dockerfile.env .

docker run \
    --network host -d \
    --name skrecovery \
    --entrypoint /bin/bash \
    -v "$(pwd)":/skrecovery \
    skrecovery \
    -c "tail -f /dev/null"

# docker run \
#     --network host -d \
#     --name skrecovery \
#     --entrypoint /usr/local/bin/python \
#     -v "$(pwd)":/skrecovery \
#     skrecovery \
#     -m experiments.recover -n 100


docker exec -it skrecovery /bin/bash
