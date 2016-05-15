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
    sudo docker port $1 >/dev/null 2>&1
    echo $?
}

wait_container()
{
    while [ "$(container_alive $1)" != 0 ]; do
        sleep ${2:-1}s
    done
}

get_link()
{
    echo ${3:-http}://$(sudo docker port $1 $2)
}

NEW_UUID=$(uuid 8)
NEW_NAME=$(name $NEW_UUID)

# ensure sudo
sudo echo hello sudo >/dev/null

(
wait_container $NEW_NAME 1
# expose 80 (http) and 443 (https) for Nginx, and 5000 for flask, 8888 for jupyter
echo -e \
    "\n\n" \
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
) & (
sudo docker run --rm -P $1 \
    --name=$NEW_NAME \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v ~/.ssh:/root/.ssh \
    -v $(pwd)/nginx-conf:/etc/nginx/conf.d \
    -v $(pwd)/workspace:/root/workspace \
    -v $(cd ../..; pwd):/root/workspace/dsd \
    dsd-console
)
