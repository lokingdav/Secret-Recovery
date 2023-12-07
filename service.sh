#!/bin/bash

valid_apps=(ledger)
valid_commands=(start stop)

app=$(echo $1 | cut -d ":" -f 1)
cmd=$(echo $1 | cut -d ":" -f 2)

function is_valid {
    local array=$1[@]
    local seeking=$2
    local in=1
    for element in "${!array}"; do
        if [[ $element == $seeking ]]; then
            in=0
            break
        fi
    done
    return $in
}


function queue:stop {
    # if rq.pid.log does not exist, then a queue worker is not running
    if [ ! -f ./logs/rq.pid.log ]
        then
        echo "Queue worker is not running"
        exit 1
    fi
    
    echo "Stopping queue worker for traceback provider"
    kill $(cat ./logs/rq.pid.log)
    rm ./logs/rq.pid.log
}

function queue:start {
    # if rq.pid.log exists, then a queue worker is already running
    if [ -f ./logs/rq.pid.log ]
        then
        echo "Queue worker is already running. Logs are in ./logs/rq.wrk.log"
        exit 1
    fi
    echo "Starting queue worker for traceback provider"
    touch ./logs/rq.pid.log
    rq worker --with-scheduler --pid ./logs/rq.pid.log > ./logs/rq.wrk.log 2>&1 &
    echo "Queue worker started. Logs are in ./logs/rq.wrk.log"
}

if ! is_valid valid_apps $app; then
    echo "Invalid app: $app. Valid apps are: ${valid_apps[@]}"
    exit 1
fi

if ! is_valid valid_commands $cmd; then
    echo "Invalid command: $cmd. Valid commands are: ${valid_commands[@]}"
    exit 1
fi


if [ $app == "ledger" ]
    then
    if [ $cmd == "start" ]
        then
        queue:start
    elif [ $cmd == "stop" ]
        then
        queue:stop
    fi
fi
