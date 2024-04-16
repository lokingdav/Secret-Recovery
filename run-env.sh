docker rm -f skrecovery

docker build -t skrecovery -f Dockerfile.env .

docker run \
    --network host -d \
    --name skrecovery \
    --entrypoint /bin/bash \
    -v "$(pwd)":/skrecovery \
    skrecovery \
    -c "tail -f /dev/null"


docker exec -it skrecovery /bin/bash
