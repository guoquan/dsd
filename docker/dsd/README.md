# DSD console

Use the Ubuntu 14:04 base image for minimum dependency.
Libraries are install according to requirement of the system:
* Nginx: front-end web server
* Python: we are python driven
* Flask: web-container
* MongoDB: NoSQL database

Don't have to use different container for different service now.

# How to

For runtime, we run detached
```bash
sudo docker run -d \
    --name dsd-console-runtime \
    -p 10080:80 -p 15000:5000 -p 18888:8888 \
    -v ~/.ssh:/root/.ssh \
    -v ~/dsd:/root/dsd \
    -v nginx-conf:/etc/nginx/conf.d \
    -v workspace:/root/workspace \
    dsd-console
```

For development time, we run clean, also expose dsd root in workspace
```bash
sudo docker run --rm \
    --name dsd-console-devel \
    -p 10080:80 -p 15000:5000 -p 18888:8888 \
    -v ~/.ssh:/root/.ssh \
    -v ~/dsd:/root/dsd \
    -v nginx-conf:/etc/nginx/conf.d \
    -v workspace:/root/workspace \
    -v ~/dsd:/root/workspace/dsd \
    dsd-console
```

Use 18888 for jupyter. Use 10080 for nginx and 15000 for flask. MongoDB is not exported.
Use `--rm` to keep it clean after running.
