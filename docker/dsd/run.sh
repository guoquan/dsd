#!/bin/bash

uuid()
{
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w ${1:-32} | head -n 1
}

name()
{
    echo dsd-console-devel-$1
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

POLL_INTERVAL=0.1
NEW_UUID=$(uuid 8)
NEW_NAME=$(name $NEW_UUID)

# ensure sudo
sudo echo hello sudo >/dev/null

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
        "\n* $(get_link $NEW_NAME 80/tcp) for nginx on http" \
        "\n* $(get_link $NEW_NAME 443/tcp https) for nginx on https" \
        "\n* $(get_link $NEW_NAME 5000/tcp) for flask" \
        "\n* $(get_link $NEW_NAME 8888/tcp) for jupyter" \
        "\n=====================================" \
        "\n\n"
else
    echo "Container not start normally. Check and try again."
fi
) & (
sudo nvidia-docker run --rm -P $@ \
    --name=$NEW_NAME \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v ~/.ssh:/root/.ssh \
    -v $(cd ../..; pwd):/root/dsd:ro \
    -v $(pwd)/nginx-conf:/etc/nginx/conf.d \
    -v $(pwd)/workspace:/root/workspace \
    -v $(cd ../..; pwd):/root/workspace/dsd \
    -v $(pwd)/volumes:/volumes \
    -v $(pwd)/data:/data \
    dsdgroup/dsd-console
sleep $(bc <<< "1 + 2 * $POLL_INTERVAL")s
)
