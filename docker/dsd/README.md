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

## Start

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

## Stop

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

## Inside

Data, files, or anything in `~/workspace` in the container will be kept within [`workspace`](../../workspace).
Avoid unnecessary files to be submitted.
For temporary files, keep them in `~/workspace/tmp` and git will ignore them.

You can read the scripts in `run.sh` and `Dockerfile` to get a clear idea about what is going on.
More information can be found in `README.md` in [`workspace`](../../workspace) for operating and in [`python`](../../python) for web app usage and development.

# How to (PRO version)

If you are a PRO, and understand each line of codes below, you can use them to start the container.
They are basically equivalent to `run.sh`.
Please avoid any conflict, for example, port assignment.

## Development

For development time, run clean, and mount local working directory in workspace for development.
```
sudo nvidia-docker run \
    --name=dsd-console-devel \
    --rm \
    -e "DSD_DEV=1" \
    -p <local_flask_port>:5000 -p <local_jupyter_port>:8888 \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.ssh:/root/.ssh:ro \
    -v <DSD_path>:/opt/dsd:ro \
    -v <DSD_path>/workspace:/root/workspace \
    -v <DSD_path>/docker/dsd/volumes:/volumes \
    -v <DSD_path>/docker/dsd/data:/data \
    -v <DSD_path>:/root/workspace/dsd \
    dsdgroup/dsd-console
```
Specify `<local_flask_port>`, `<local_jupyter_port>`, and `<DSD_path>` to run the container.
Be sure to use absolute path. Otherwise it could conflict with volume-driver plugin of nvidia-docker.

Following are the meaning of each parameter.
* `--name=dsd-console-devel` specifies a name of the container.
* `--rm` requires docker to clean up (remove) the container after process exit.
* `-e "DSD_DEV=1"` sets an environment variable in the container to identify development mode.
* `-p <local_flask_port>:5000 -p <local_jupyter_port>:8888` specifies ports to visit `jupyer` for development and `flask` for the web app.
* `--add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }')` detects host IP and specifies a host name in the container to communicate with the host.
* `-v /var/run/docker.sock:/var/run/docker.sock` mounts Docker sock in to the container for Docker API access.
* `-v ~/.ssh:/root/.ssh:ro` mounts `ssh-key`s of the current user to have the same git (and any service using such keys) privilege of the user. They are read-only.
* `-v <DSD_path>/<some_path>:<some_path>` mounts some directories to container for dsd-console.
    * `/opt/dsd` is where we mount the working directory for running tye system. This is read-only.
    * `/root/workspace` is the default workspace of `dsd-console`, containing a serial of scripts to work with the web app.
    * `/volumes` is the mount point for containing end user volumes.
    * `/data` is the mount point for containing public data.
* `-v <DSD_path>:/root/workspace/dsd` mounts the working directory within workspace for the convenience of development.

## Runtime

For runtime, run detached, prevent failure, and with formal (but limited) port assignment.
```
sudo nvidia-docker run \
    --name=dsd-console-runtime \
    -d --restart=on-failure \
    -e "DSD_DEV=0" \
    -p <local_flask_port>:5000 \
    --add-host=dockerhost:$(ip route | awk '/docker0/ { print $NF }') \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v <DSD_path>:/opt/dsd:ro \
    -v <DSD_path>/workspace:/root/workspace \
    -v <DSD_path>/docker/dsd/volumes:/volumes \
    -v <DSD_path>/docker/dsd/data:/data \
    dsdgroup/dsd-console
    bash start.sh
```
Most of the parameters are the same with development mode.

Special parameters are as follows.
* `-d --restart=on-failure` let the container run in the background (detached) and assign a restart policy to restart on failure.
* `bash start.sh` override the command to be executed in the container to start web app directly. For more about `start.sh`, check out `README.md` in [`workspace`](../../workspace).
* `--rm`, `-p <local_jupyter_port>:8888`, and `-v <DSD_path>:/root/workspace/dsd` are removed.

If you are sure you understand above code, it is OK just to run it in your own way.

## Examples
An example to run DSD Console in development mode on OSX with boot2docker(in VM) and Kitematic is as follows.
```
docker run \
    --name=dsd-console-devel \
    -e "DSD_DEV=1" \
    -p 5000:5000 -p 8888:8888 \
    --add-host=dockerhost:192.168.99.100 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    dsdgroup/dsd-console
```
Later, you can modify other directories mounting on Kitematic interface.
But never touch `/var/run/docker.sock`, because Kitematic cannot resolve it in fact.

I also found that it may have problem with privilege of `docker/dsd/data` that prevent MongoDB starting normally.
Just don't set that path in this case.

You can also try using TLS in above environment.
```
docker run \
    --name=dsd-console-devel-certs \
    -e "DSD_DEV=1" \
    -p 5000:5000 -p 8888:8888 \
    --add-host=dockerhost:192.168.99.100 \
    -v ~/.docker/machine/certs:/root/.docker \
    dsdgroup/dsd-console
```
