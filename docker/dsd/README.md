# DSD console

Use the Ubuntu 14:04 base image for minimum dependency.
Libraries are install according to requirement of the system:
* Nginx: front-end web server
* Python: we are python driven
* Flask: web-container
* MongoDB: NoSQL database

Don't have to use different container for different service now.

# How to (simple version)

For development, use the `run.sh` script.

```bash
chmod u+x run.sh
./run.sh
```

Follow the notification to use provided links. Ports are automatically assigned.
To stop it, use `Ctrl-c` to terminate the `jupyter` process and the container will be destroy automatically.
Note that closing the terminal will also terminate the process.
Data, files, or anything in `~/workspace` in the container will be kept within `dsd/docker/dsd/workspace`.
Directory `/etc/nginx/conf.d` in the container maps `dsd/docker/dsd/nginx-conf`.
Changes to `~/workspace/dsd` in the container will also reflect to the project root directory `dsd`.

# How to (PRO version)

If you are a PRO, and understand each line of codes below, you can use them to start the container.
They are basically equivalent to `run.sh`.
Please avoid any conflict, for example, port assignment.

For runtime, run detached and with formal port assignment.
```bash
sudo nvidia-docker run -d \
    --name=dsd-console-runtime \
    -p 80:80 -p 5000:5000 -p 8888:8888 \
    -v ~/.ssh:/root/.ssh \
    -v $(cd ../..; pwd):/root/dsd \
    -v $(pwd)/nginx-conf:/etc/nginx/conf.d \
    -v $(pwd)/workspace:/root/workspace \
    dsdgroup/dsd-console
```

For development time, run clean, also expose dsd root in workspace for development
```bash
sudo nvidia-docker run --rm \
    --name=dsd-console-devel \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -p 10080:80 -p 15000:5000 -p 18888:8888 \
    -v ~/.ssh:/root/.ssh \
    -v $(cd ../..; pwd):/root/dsd \
    -v $(pwd)/nginx-conf:/etc/nginx/conf.d \
    -v $(pwd)/workspace:/root/workspace \
    -v $(cd ../..; pwd):/root/workspace/dsd \
    dsdgroup/dsd-console
```

The code above uses port 18888 for jupyter, 10080 for nginx, and 15000 for flask.
MongoDB is not exported.
Use `--rm` to keep it clean after running.
