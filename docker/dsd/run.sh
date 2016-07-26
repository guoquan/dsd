#!/bin/bash

POLL_INTERVAL=0.1

uuid()
{
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w ${1:-32} | head -n 1
}

name()
{
    if [[ $2 -eq 1 ]]; then
        echo dsd-console-devel-$1
    else
        echo dsd-console-runtime-$1
    fi
}

container_alive()
{
    [[ ! -z $(sudo docker ps -aq -f name=$1) ]]
}

wait_container()
{
    WAIT_COUNT=0
    DEC=("-" "\\" "|" "/")
    while ! $(container_alive $1); do
        printf "\r[ ${DEC[$(( $WAIT_COUNT % ${#DEC[@]} ))]} ] [ Time elapsed: $(bc <<< "$WAIT_COUNT * ${2:-1}") ] "
        ((WAIT_COUNT++))
        sleep ${2:-1}s
    done
}

get_link()
{
    IF="$(route | grep "default" | awk '{OFS=" "}{ print $NF }')"
    IP="$(ip route | awk 'NR>1 && /'$IF'/ {print $NF}')"
    echo ${3:-http}://$(sudo docker port $1 $2 | sed 's/0.0.0.0/'$IP'/g')
}

# runtime/dev
if [[ ! -z "$1" ]] && [[ "$1" -eq "--dev" ]]; then
    DEV=1
    shift
else
    DEV=0
fi

# ensure sudo
sudo echo hello sudo >/dev/null

NEW_UUID=$(uuid 8)
NEW_NAME=$(name $NEW_UUID $DEV)

(
wait_container $NEW_NAME $POLL_INTERVAL
sleep 1s; if $(container_alive $NEW_NAME); then
    # expose 80 (http) and 443 (https) for Nginx, and 5000 for flask, 8888 for jupyter
    echo -e \
        "\n" \
        "\n=====================================" \
        "\nContainer: $NEW_NAME" \
        "\n-------------------------------------" \
        "\nUse the following links:" \
        "\n* $(get_link $NEW_NAME 5000/tcp) for flask" \
        "\n* $(get_link $NEW_NAME 8888/tcp) for jupyter" \
        "\n=====================================" \
        "\n\n"
else
    echo "Container not start normally. Check and try again."
fi
) & (
if [[ $DEV -eq 1 ]]; then
    sudo nvidia-docker run \
        --name=$NEW_NAME \
        --rm \
        -e "DSD_DEV=$DEV" \
        -P \
        --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v ~/.ssh:/root/.ssh \
        -v $(cd ../..; pwd):/root/dsd:ro \
        -v $(pwd)/workspace:/root/workspace \
        -v $(pwd)/volumes:/volumes \
        -v $(pwd)/data:/data \
        -v $(cd ../..; pwd):/root/workspace/dsd \
        dsdgroup/dsd-console
else
    sudo nvidia-docker run \
        --name=$NEW_NAME \
        --rm \
        -e "DSD_DEV=$DEV" \
        -p 5000 \
        --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v $(cd ../..; pwd):/root/dsd:ro \
        -v $(pwd)/workspace:/root/workspace \
        -v $(pwd)/volumes:/volumes \
        -v $(pwd)/data:/data \
        dsdgroup/dsd-console \
        bash start.sh $@
fi
sleep $(bc <<< "1 + 2 * $POLL_INTERVAL")s
)
