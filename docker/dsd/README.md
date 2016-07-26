# DSD console

Use the Ubuntu 14:04 base image for minimum dependency.
Libraries are install according to requirement of the system:
* Python: we are python driven
* Flask: web-container
* MongoDB: NoSQL database

Don't have to use different container for different service now.
We run web app and database together in one place.

# How to (simple version)

Basically, use the `run.sh` script.
For development, run with `dev`
```
bash run.sh dev
```
For runtime deployment, run without `dev`
```
bash run.sh
```
You can append any parameters.
They will be passed to the [initialization script](../../workspace/start.sh) of DSD console.
In `dev` mode, extra parameters will be discard, because you can always type them inside the development environment.

Follow the notification to use provided links. Ports are automatically assigned.

Notice that, development mode runs the container in an attached manner that will display log information from jupyter.
To stop it, use `Ctrl-c` to terminate the `jupyter` process and the container will be destroy automatically.
Closing the `tty` will also terminate the process.

Runtime mode runs the container detached.
To stop it, use Docker `stop` command.
```
sudo docker stop dsd-console-runtime
```
The container can be started again using Docker `start` command
```
sudo docker start dsd-console-runtime
```
or simply use `run.sh` script again.
The script will try to detect existing DSD console runtime container and `start` it rather than to `run` a new one.

Data, files, or anything in `~/workspace` in the container will be kept within `dsd/docker/dsd/workspace`.
Avoid unnecessary files to be submitted.
For temporary files, keep them in `~/workspace/tmp` and git will ignore them.

You can read the scripts in `run.sh` and `Dockerfile` to get a clear idea about what is going on.

# How to (PRO version)

If you are a PRO, and understand each line of codes below, you can use them to start the container.
They are basically equivalent to `run.sh`.
Please avoid any conflict, for example, port assignment.

For development time, run clean, also expose dsd root in workspace for development
```
sudo nvidia-docker run \
    --name=dsd-console-devel \
    --rm \
    -e "DSD_DEV=1" \
    -p <local_flask_port>:5000 -p <local_jupyter_port>:8888\
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.ssh:/root/.ssh \
    -v <DSD_path>:/opt/dsd:ro \
    -v <DSD_path>/workspace:/root/workspace \
    -v <DSD_path>/docker/dsd/volumes:/volumes \
    -v <DSD_path>/docker/dsd/data:/data \
    -v <DSD_path>:/root/workspace/dsd \
    dsdgroup/dsd-console
```

For runtime, run detached and with formal port assignment.
```
sudo nvidia-docker run \
    --name=dsd-console-runtime \
    -d --restart=on-failure \
    -e "DSD_DEV=0" \
    -p <local_flask_port>:5000 \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.ssh:/root/.ssh \
    -v <DSD_path>:/opt/dsd:ro \
    -v <DSD_path>/workspace:/root/workspace \
    -v <DSD_path>/docker/dsd/volumes:/volumes \
    -v <DSD_path>/docker/dsd/data:/data \
    dsdgroup/dsd-console
    bash start.sh
```
